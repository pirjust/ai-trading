"""
策略管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from app.models.strategy import Strategy

router = APIRouter()

@router.get("/")
async def get_strategies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Strategy]:
    """获取策略列表"""
    strategies = db.query(Strategy).offset(skip).limit(limit).all()
    return strategies

@router.post("/")
async def create_strategy(
    name: str,
    description: str,
    strategy_type: str,
    config: dict,
    db: Session = Depends(get_db)
):
    """创建新策略"""
    strategy = Strategy(
        name=name,
        description=description,
        strategy_type=strategy_type,
        config=config,
        status="inactive"
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    
    return {"message": "策略创建成功", "strategy_id": strategy.id}

@router.put("/{strategy_id}/activate")
async def activate_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """激活策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategy.status = "active"
    db.commit()
    
    return {"message": "策略已激活"}

@router.put("/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """停用策略"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategy.status = "inactive"
    db.commit()
    
    return {"message": "策略已停用"}