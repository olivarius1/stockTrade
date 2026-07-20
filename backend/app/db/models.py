from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.db.session import Base

class KlineData(Base):
    """K线数据表，存储前复权日K线数据。增量更新，不修改历史记录。"""
    __tablename__ = "kline_data"
    __table_args__ = (
        UniqueConstraint("stock_code", "date", name="uq_kline_data_stock_date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    amount = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ValuationHistory(Base):
    """估值历史表，每日估值评分记录。用于趋势分析和百分位计算。

    数据库层面通过 (stock_code, date) 唯一约束保证每日每只股票只有一条记录，
    从源头杜绝多任务并发写入或重复触发产生的重复数据。
    """
    __tablename__ = "valuation_history"
    __table_args__ = (
        UniqueConstraint("stock_code", "date", name="uq_valuation_history_stock_date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    date = Column(Date, index=True)
    score = Column(Float)
    pe_score = Column(Float)
    pb_score = Column(Float)
    peg_score = Column(Float)
    ma_score = Column(Float)
    volatility_score = Column(Float)
    volume_score = Column(Float)
    roe_score = Column(Float)
    dividend_score = Column(Float)
    ai_score = Column(Float)
    pe = Column(Float)
    pb = Column(Float)
    price = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FinancialData(Base):
    """财务数据表，存储季报/年报数据。更新频率用户可配置。"""
    __tablename__ = "financial_data"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), index=True)
    report_date = Column(Date, index=True)
    eps = Column(Float)
    revenue = Column(Float)
    net_profit = Column(Float)
    roe = Column(Float)
    gross_margin = Column(Float)
    dividend_rate = Column(Float)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class StockGroup(Base):
    """股票分组表，支持用户自定义分组管理。"""
    __tablename__ = "stock_group"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

class Watchlist(Base):
    """自选股表，记录用户关注的股票及其估值模型配置。"""
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), unique=True, index=True)
    stock_name = Column(String(50))
    industry = Column(String(50))
    model_type = Column(String(20))
    ai_enabled = Column(Boolean, default=False)
    group_id = Column(Integer, nullable=True)  # 关联 StockGroup，NULL=默认"自选"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SchedulerConfig(Base):
    """定时任务配置表，用户可在设置页面调整频率。"""
    __tablename__ = "scheduler_config"
    id = Column(Integer, primary_key=True, index=True)
    schedule_type = Column(String(20))
    cron_expression = Column(String(50))
    enabled = Column(Boolean, default=True)
    include_ai = Column(Boolean, default=False)
    financial_update_frequency = Column(Integer, default=7)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ModelConfig(Base):
    """估值模型配置表，存储因子组合和权重。支持插件化模型管理。"""
    __tablename__ = "model_config"
    id = Column(Integer, primary_key=True, index=True)
    model_code = Column(String(20), unique=True, index=True)
    model_name = Column(String(50))
    factors = Column(JSON)
    weights = Column(JSON)
    params = Column(JSON)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    """用户表，单用户密码认证。"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=func.now())

class TaskProgress(Base):
    """批量任务执行记录表，持久化每次任务的执行结果。"""
    __tablename__ = "task_progress"
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), index=True)  # 任务类型: kline_batch_fetch
    status = Column(String(20), default="running")  # running / completed / failed
    total = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    started_at = Column(DateTime, default=func.now())
    finished_at = Column(DateTime, nullable=True)
    error_detail = Column(JSON, nullable=True)  # 失败详情
