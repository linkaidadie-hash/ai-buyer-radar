"""跟进管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# 类定义必须在使用之前
class FollowupCreate(BaseModel):
    method: str
    subject: Optional[str] = None
    content: str
    result: Optional[str] = None
    next_followup: Optional[str] = None
    followup_date: Optional[str] = None


@router.get("/{buyer_id}")
async def get_followups(buyer_id: int):
    """获取跟进记录"""
    from services.database import get_conn, get_followups as db_get_followups
    with get_conn() as conn:
        return db_get_followups(conn, buyer_id)


@router.post("/{buyer_id}")
async def add_followup(buyer_id: int, data: FollowupCreate):
    """添加跟进"""
    from services.database import (get_conn, add_followup as db_add_followup, 
                                   get_buyer, update_buyer)
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        fid = db_add_followup(conn, buyer_id, data.model_dump())
        if data.followup_date:
            update_buyer(conn, buyer_id, {"status": "contacted"})
    return {"id": fid, "message": "添加成功"}


@router.get("/due/list")
async def get_followup_due():
    """待跟进列表"""
    from services.database import get_followup_due as db_get_followup_due
    return db_get_followup_due()