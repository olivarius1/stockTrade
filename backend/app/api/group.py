"""分组管理API，提供股票自定义分组的CRUD操作。"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import StockGroup, Watchlist
from app.schemas.watchlist import StockGroupCreate, StockGroupResponse

router = APIRouter()


@router.get("", response_model=List[StockGroupResponse])
def get_groups(db: Session = Depends(get_db)):
    """获取所有分组（含各分组股票数量）。"""
    groups = db.query(StockGroup).order_by(StockGroup.sort_order).all()
    result = []
    for g in groups:
        count = db.query(func.count(Watchlist.id)).filter(Watchlist.group_id == g.id).scalar()
        result.append(StockGroupResponse(
            id=g.id, name=g.name, sort_order=g.sort_order, stock_count=count
        ))
    return result


@router.post("", response_model=StockGroupResponse)
def create_group(item: StockGroupCreate, db: Session = Depends(get_db)):
    """创建新分组。"""
    existing = db.query(StockGroup).filter(StockGroup.name == item.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="分组名已存在")
    group = StockGroup(name=item.name, sort_order=item.sort_order)
    db.add(group)
    db.commit()
    db.refresh(group)
    return StockGroupResponse(id=group.id, name=group.name, sort_order=group.sort_order, stock_count=0)


@router.put("/{group_id}", response_model=StockGroupResponse)
def rename_group(group_id: int, item: StockGroupCreate, db: Session = Depends(get_db)):
    """重命名分组。"""
    group = db.query(StockGroup).filter(StockGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    # 检查名称唯一性
    dup = db.query(StockGroup).filter(StockGroup.name == item.name, StockGroup.id != group_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="分组名已存在")
    group.name = item.name
    group.sort_order = item.sort_order
    db.commit()
    db.refresh(group)
    count = db.query(func.count(Watchlist.id)).filter(Watchlist.group_id == group.id).scalar()
    return StockGroupResponse(id=group.id, name=group.name, sort_order=group.sort_order, stock_count=count)


@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """删除分组，组内股票回归默认自选（group_id置NULL）。"""
    group = db.query(StockGroup).filter(StockGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    # 组内股票回归默认
    db.query(Watchlist).filter(Watchlist.group_id == group_id).update({"group_id": None})
    db.delete(group)
    db.commit()
    return {"message": "分组已删除，股票已回归自选"}
