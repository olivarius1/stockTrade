"""自选股管理服务，提供自选股的增删查和批量估值计算。

批量计算在 Celery 定时任务和 API 中复用，确保逻辑一致。
"""
from typing import Dict, List, Optional
from app.db.models import Watchlist, ValuationHistory, KlineData
from app.services.valuation import ValuationService
from app.services.data_service import DataService
from app.data.kline_manager import update_kline


class WatchlistService:
    """自选股服务，管理自选股列表并触发估值计算。"""

    def __init__(self):
        self.valuation_service = ValuationService()
        self.data_service = DataService()

    def get_watchlist(self, db) -> List[Dict]:
        """查询全部自选股并返回其序列化信息列表。"""
        items = db.query(Watchlist).all()
        return [
            {
                "id": item.id,
                "stock_code": item.stock_code,
                "stock_name": item.stock_name,
                "industry": item.industry,
                "model_type": item.model_type,
                "ai_enabled": item.ai_enabled,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in items
        ]

    def add_stock(self, db, stock_code: str, stock_name: str, industry: str, model_type: str, ai_enabled: bool = False):
        """添加一只股票到自选股列表，重复添加会被拒绝。

        Args:
            db: 数据库会话。
            stock_code: 股票代码，唯一标识。
            stock_name: 股票名称。
            industry: 所属行业。
            model_type: 适用的估值模型代码。
            ai_enabled: 是否启用 AI 因子，默认 False。

        Returns:
            新增自选股的序列化字典。

        Raises:
            ValueError: 股票已存在于自选股列表时抛出。
        """
        existing = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if existing:
            raise ValueError(f"Stock {stock_code} already exists in watchlist")

        item = Watchlist(
            stock_code=stock_code,
            stock_name=stock_name,
            industry=industry,
            model_type=model_type,
            ai_enabled=ai_enabled,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {
            "id": item.id,
            "stock_code": item.stock_code,
            "stock_name": item.stock_name,
            "industry": item.industry,
            "model_type": item.model_type,
            "ai_enabled": item.ai_enabled,
        }

    def remove_stock(self, db, stock_code: str):
        """从自选股列表移除指定股票。

        Args:
            db: 数据库会话。
            stock_code: 待移除的股票代码。

        Returns:
            包含 stock_code 与 removed=True 的字典。

        Raises:
            ValueError: 股票不在自选股列表中时抛出。
        """
        item = db.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
        if not item:
            raise ValueError(f"Stock {stock_code} not found in watchlist")

        db.delete(item)
        db.commit()
        return {"stock_code": stock_code, "removed": True}

    def save_valuation_history(self, db, stock_code: str, calc_date, score: float,
                               factors: dict, pe: float, pb: float, price: float):
        """保存或更新当日估值历史记录（upsert）。

        同一股票同一天只保留一条记录，重复写入时更新最新值，避免多任务
        并发或重复触发产生重复条目，导致百分位计算失真。

        Args:
            db: 数据库会话。
            stock_code: 股票代码。
            calc_date: 估值日期（date 对象）。
            score: 总估值分。
            factors: 各因子得分数典。
            pe: 市盈率。
            pb: 市净率。
            price: 最新价格。
        """
        existing = db.query(ValuationHistory).filter(
            ValuationHistory.stock_code == stock_code,
            ValuationHistory.date == calc_date
        ).first()

        if existing:
            existing.score = score
            existing.pe_score = factors.get("pe")
            existing.pb_score = factors.get("pb")
            existing.peg_score = factors.get("peg")
            existing.ma_score = factors.get("ma_deviation")
            existing.volatility_score = factors.get("volatility")
            existing.volume_score = factors.get("volume")
            existing.roe_score = factors.get("roe")
            existing.dividend_score = factors.get("dividend")
            existing.ai_score = factors.get("ai_analysis")
            existing.pe = pe
            existing.pb = pb
            existing.price = price
        else:
            history = ValuationHistory(
                stock_code=stock_code,
                date=calc_date,
                score=score,
                pe_score=factors.get("pe"),
                pb_score=factors.get("pb"),
                peg_score=factors.get("peg"),
                ma_score=factors.get("ma_deviation"),
                volatility_score=factors.get("volatility"),
                volume_score=factors.get("volume"),
                roe_score=factors.get("roe"),
                dividend_score=factors.get("dividend"),
                ai_score=factors.get("ai_analysis"),
                pe=pe,
                pb=pb,
                price=price,
            )
            db.add(history)

        db.commit()

    def backfill_valuation_history(self, db, stock_code: str, model_type: str,
                                   ai_enabled: bool = False) -> Optional[Dict]:
        """用现有K线历史批量回溯估值并保存到数据库。

        新加入自选股的股票往往有大量K线历史但无估值历史，导致百分位和分级
        无法基于个股自身分布计算。本方法遍历全部历史K线，逐日推算指标并
        计算估值分，一次性补齐历史。

        回溯逻辑：
        1. 从数据库读取完整K线历史（close, volume）
        2. 获取最新财务数据（eps, roe）
        3. 对每一天：
           - price = close
           - pe = close / eps（用最新eps估算历史PE，近似）
           - pb = pe * roe（利用 PB = PE × ROE 关系推算，近似）
           - ma20/ma60/volatility/volume_ratio 从历史序列计算
        4. 调用估值模型计算得分
        5. 批量保存到 valuation_history

        注意：由于使用最新EPS/ROE估算历史PE/PB，回溯结果有一定近似性；
        后续定时任务会用当日实时PE/PB逐步更新改善。

        Args:
            db: 数据库会话。
            stock_code: 股票代码。
            model_type: 估值模型代码。
            ai_enabled: 是否启用AI因子。

        Returns:
            包含 backfilled(条数)、from_date、to_date 的字典；
            K线不足60天无法计算MA/波动率时返回 None。
        """
        # 1. 读取完整K线历史
        kline_rows = db.query(KlineData).filter(
            KlineData.stock_code == stock_code
        ).order_by(KlineData.date).all()

        if len(kline_rows) < 60:
            return None

        # 2. 最新财务数据
        financial = self.data_service.get_financial_data(stock_code, db=db)
        eps = financial.get("eps", 0) or 1e-6  # 避免除零
        roe = financial.get("roe", 0) or 0

        closes = [r.close for r in kline_rows]
        volumes = [r.volume for r in kline_rows]

        backfilled = 0
        from_date = kline_rows[0].date
        to_date = kline_rows[-1].date

        # 3. 逐日回溯
        for i, row in enumerate(kline_rows):
            price = row.close

            # PE/PB 用最新财务数据推算（近似）
            pe = price / eps if eps > 0 else 0
            pb = pe * roe if roe > 0 else 0

            # 技术指标从历史序列计算
            hist_closes = closes[:i + 1]
            hist_volumes = volumes[:i + 1]

            ma20 = self.data_service.calculate_ma(stock_code, hist_closes, period=20)
            ma60 = self.data_service.calculate_ma(stock_code, hist_closes, period=60)
            volatility = self.data_service.calculate_volatility(stock_code, hist_closes)

            avg_volume = sum(hist_volumes[-60:]) / min(len(hist_volumes), 60) if hist_volumes else 1
            volume_ratio = row.volume / avg_volume if avg_volume else 1

            data = {
                "price": price,
                "pe": pe,
                "pb": pb,
                "volume": row.volume,
                "amount": 0,
                "ma20": ma20,
                "ma60": ma60,
                "volatility": volatility,
                "volume_ratio": volume_ratio,
                "eps": financial.get("eps", 0),
                "revenue": financial.get("revenue", 0),
                "net_profit": financial.get("net_profit", 0),
                "roe": financial.get("roe", 0),
                "gross_margin": financial.get("gross_margin", 0),
                "dividend_rate": financial.get("dividend_rate", 0),
            }

            try:
                result = self.valuation_service.calculate(
                    stock_code, model_type, data, ai_enabled=ai_enabled
                )
                factors = result.get("factors", {})
                score = result.get("score", 0)

                # 使用内部upsert但不commit，最后统一commit
                existing = db.query(ValuationHistory).filter(
                    ValuationHistory.stock_code == stock_code,
                    ValuationHistory.date == row.date
                ).first()

                if existing:
                    existing.score = score
                    existing.pe_score = factors.get("pe")
                    existing.pb_score = factors.get("pb")
                    existing.peg_score = factors.get("peg")
                    existing.ma_score = factors.get("ma_deviation")
                    existing.volatility_score = factors.get("volatility")
                    existing.volume_score = factors.get("volume")
                    existing.roe_score = factors.get("roe")
                    existing.dividend_score = factors.get("dividend")
                    existing.ai_score = factors.get("ai_analysis")
                    existing.pe = pe
                    existing.pb = pb
                    existing.price = price
                else:
                    history = ValuationHistory(
                        stock_code=stock_code,
                        date=row.date,
                        score=score,
                        pe_score=factors.get("pe"),
                        pb_score=factors.get("pb"),
                        peg_score=factors.get("peg"),
                        ma_score=factors.get("ma_deviation"),
                        volatility_score=factors.get("volatility"),
                        volume_score=factors.get("volume"),
                        roe_score=factors.get("roe"),
                        dividend_score=factors.get("dividend"),
                        ai_score=factors.get("ai_analysis"),
                        pe=pe,
                        pb=pb,
                        price=price,
                    )
                    db.add(history)

                backfilled += 1
            except Exception:
                # 单日计算失败不影响其他天
                continue

        db.commit()
        return {
            "backfilled": backfilled,
            "from_date": str(from_date),
            "to_date": str(to_date),
        }

    def incremental_calculate(self, db, stock_code: str, model_type: str,
                              ai_enabled: bool = False) -> Dict:
        """增量计算：查看K线范围，补齐缺失的估值历史。

        逻辑：
        1. 查看最早K线日期，如果估值历史缺少早期数据，向前补齐
        2. 查看最新K线日期，如果估值历史缺少近期数据，向后补齐

        Args:
            db: 数据库会话。
            stock_code: 股票代码。
            model_type: 估值模型代码。
            ai_enabled: 是否启用AI因子。

        Returns:
            包含 added(新增条数)、total_kline、total_valuation 的字典。
        """
        # 先从API增量拉取K线数据（确保本地K线是最新的）
        try:
            update_kline(stock_code)
        except Exception:
            pass  # 网络失败时仍尝试用已有数据

        # 获取K线日期范围
        kline_rows = db.query(KlineData).filter(
            KlineData.stock_code == stock_code
        ).order_by(KlineData.date).all()

        if not kline_rows:
            return {"added": 0, "total_kline": 0, "total_valuation": 0, "message": "无K线数据（API拉取失败）"}

        # 已有估值历史的日期集合
        existing_dates = set(
            r[0] for r in db.query(ValuationHistory.date).filter(
                ValuationHistory.stock_code == stock_code
            ).all()
        )

        # 找出所有缺少估值记录的K线日期
        missing_rows = [r for r in kline_rows if r.date not in existing_dates]

        if not missing_rows:
            return {
                "added": 0,
                "total_kline": len(kline_rows),
                "total_valuation": len(existing_dates),
                "message": "无需补齐",
            }

        # 财务数据（用于估算历史PE/PB）
        financial = self.data_service.get_financial_data(stock_code, db=db)
        eps = financial.get("eps", 0) or 1e-6
        roe = financial.get("roe", 0) or 0

        closes = [r.close for r in kline_rows]
        volumes = [r.volume for r in kline_rows]
        date_to_idx = {r.date: i for i, r in enumerate(kline_rows)}

        added = 0
        for row in missing_rows:
            i = date_to_idx[row.date]
            price = row.close
            pe = price / eps if eps > 0 else 0
            pb = pe * roe if roe > 0 else 0

            hist_closes = closes[:i + 1]
            hist_volumes = volumes[:i + 1]

            ma20 = self.data_service.calculate_ma(stock_code, hist_closes, period=20)
            ma60 = self.data_service.calculate_ma(stock_code, hist_closes, period=60)
            volatility = self.data_service.calculate_volatility(stock_code, hist_closes)

            avg_volume = sum(hist_volumes[-60:]) / min(len(hist_volumes), 60) if hist_volumes else 1
            volume_ratio = row.volume / avg_volume if avg_volume else 1

            data = {
                "price": price,
                "pe": pe,
                "pb": pb,
                "volume": row.volume,
                "amount": 0,
                "ma20": ma20,
                "ma60": ma60,
                "volatility": volatility,
                "volume_ratio": volume_ratio,
                "eps": financial.get("eps", 0),
                "revenue": financial.get("revenue", 0),
                "net_profit": financial.get("net_profit", 0),
                "roe": financial.get("roe", 0),
                "gross_margin": financial.get("gross_margin", 0),
                "dividend_rate": financial.get("dividend_rate", 0),
            }

            try:
                result = self.valuation_service.calculate(
                    stock_code, model_type, data, ai_enabled=ai_enabled
                )
                factors = result.get("factors", {})
                score = result.get("score", 0)

                history = ValuationHistory(
                    stock_code=stock_code,
                    date=row.date,
                    score=score,
                    pe_score=factors.get("pe"),
                    pb_score=factors.get("pb"),
                    peg_score=factors.get("peg"),
                    ma_score=factors.get("ma_deviation"),
                    volatility_score=factors.get("volatility"),
                    volume_score=factors.get("volume"),
                    roe_score=factors.get("roe"),
                    dividend_score=factors.get("dividend"),
                    ai_score=factors.get("ai_analysis"),
                    pe=pe,
                    pb=pb,
                    price=price,
                )
                db.add(history)
                added += 1
            except Exception:
                continue

        db.commit()
        return {
            "added": added,
            "total_kline": len(kline_rows),
            "total_valuation": len(existing_dates) + added,
        }

    def batch_calculate(self, db) -> List[Dict]:
        """批量计算自选股列表中所有股票的估值评分。

        为什么每次都写 DB：估值评分依赖历史趋势分析，DB 持久化支持
        后续回测与百分位计算，缺失历史数据会导致 percentile 失真。

        对历史数据不足的股票，自动从 K 线回溯填充估值历史，确保报告页曲线有数据。

        Args:
            db: 数据库会话。

        Returns:
            每只股票的计算结果列表，元素包含 stock_code、stock_name、
            score 与 status（success / no_data / error）。
        """
        items = db.query(Watchlist).all()
        results: List[Dict] = []

        for item in items:
            stock_code = item.stock_code
            stock_name = item.stock_name
            try:
                # 先从API拉取K线数据到本地数据库
                try:
                    update_kline(stock_code)
                    db.expire_all()  # psycopg2写入后刷新ORM缓存
                except Exception:
                    pass  # 网络失败时仍尝试用已有数据

                # 检查历史数据是否充足，不足则从 K 线回溯填充
                history_count = db.query(ValuationHistory).filter(
                    ValuationHistory.stock_code == stock_code
                ).count()
                if history_count < 30:
                    self.backfill_valuation_history(db, stock_code, item.model_type, item.ai_enabled)

                kline_data = self.data_service.get_kline_data(stock_code, db=db)
                if not kline_data:
                    results.append({
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "score": None,
                        "status": "no_data",
                    })
                    continue

                stock_info = kline_data[0]
                historical = kline_data[1:]

                price = stock_info.get("price", 0)
                pe = stock_info.get("pe", 0)
                pb = stock_info.get("pb", 0)
                volume = stock_info.get("volume", 0)

                closes = [h["close"] for h in historical if h.get("close") is not None]
                ma20 = self.data_service.calculate_ma(stock_code, closes, period=20)
                ma60 = self.data_service.calculate_ma(stock_code, closes, period=60)
                volatility = self.data_service.calculate_volatility(stock_code, closes)

                volumes = [h["volume"] for h in historical if h.get("volume") is not None]
                if volumes:
                    avg_volume = sum(volumes) / len(volumes)
                    volume_ratio = volume / avg_volume if avg_volume else 1
                else:
                    volume_ratio = 1

                financial = self.data_service.get_financial_data(stock_code, db=db)

                data = {
                    "price": price,
                    "pe": pe,
                    "pb": pb,
                    "volume": volume,
                    "amount": stock_info.get("amount", 0),
                    "ma20": ma20,
                    "ma60": ma60,
                    "volatility": volatility,
                    "volume_ratio": volume_ratio,
                    "eps": financial.get("eps", 0),
                    "revenue": financial.get("revenue", 0),
                    "net_profit": financial.get("net_profit", 0),
                    "roe": financial.get("roe", 0),
                    "gross_margin": financial.get("gross_margin", 0),
                    "dividend_rate": financial.get("dividend_rate", 0),
                }

                result = self.valuation_service.calculate(
                    stock_code, item.model_type, data, ai_enabled=item.ai_enabled
                )

                factors = result.get("factors", {})
                score = result.get("score", 0)
                today = self.data_service.get_current_date()

                self.save_valuation_history(db, stock_code, today, score, factors, pe, pb, price)

                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "score": score,
                    "status": "success",
                })

            except Exception as e:
                db.rollback()
                results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "score": None,
                    "status": "error",
                    "error": str(e),
                })

        return results
