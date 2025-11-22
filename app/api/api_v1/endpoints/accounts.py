"""
账户管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from app.models.account import TradingAccount

router = APIRouter()

@router.get("/")
async def get_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取账户列表"""
    accounts = db.query(TradingAccount).offset(skip).limit(limit).all()
    return accounts

@router.post("/")
async def create_account(
    account_name: str,
    account_type: str,
    exchange: str,
    api_key: str,
    api_secret: str,
    db: Session = Depends(get_db)
):
    """创建交易账户"""
    account = TradingAccount(
        account_name=account_name,
        account_type=account_type,
        exchange=exchange,
        api_key=api_key,
        api_secret=api_secret,
        status="active"
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {"message": "账户创建成功", "account_id": account.id}

@router.get("/balance/{account_id}")
async def get_account_balance(account_id: int, db: Session = Depends(get_db)):
    """获取账户余额"""
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    # 这里应该调用交易所API获取实时余额
    return {
        "account_id": account.id,
        "total_balance": 10000.0,
        "available_balance": 8000.0,
        "frozen_balance": 2000.0
    }