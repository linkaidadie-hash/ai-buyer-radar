"""联系人管理路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

router = APIRouter()


# 类定义必须在使用之前
class ContactCreate(BaseModel):
    buyer_id: int
    name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    source: Optional[str] = None
    is_primary: Optional[int] = 0


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None
    is_primary: Optional[int] = None


@router.get("/{buyer_id}")
async def get_contacts(buyer_id: int):
    """获取采购商联系人"""
    from services.database import get_conn, get_contacts as db_get_contacts
    with get_conn() as conn:
        return db_get_contacts(conn, buyer_id)


@router.post("/{buyer_id}")
async def add_contact(buyer_id: int, data: ContactCreate):
    """添加联系人"""
    from services.database import get_conn, add_contact as db_add_contact, get_buyer
    with get_conn() as conn:
        buyer = get_buyer(conn, buyer_id)
        if not buyer:
            raise HTTPException(status_code=404, detail="采购商不存在")
        contact_id = db_add_contact(conn, buyer_id, data.model_dump())
    return {"id": contact_id, "message": "添加成功"}


@router.put("/{contact_id}")
async def update_contact(contact_id: int, data: ContactUpdate):
    """更新联系人"""
    from services.database import get_conn, update_contact as db_update_contact
    with get_conn() as conn:
        success = db_update_contact(conn, contact_id, data.model_dump(exclude_none=True))
        if not success:
            raise HTTPException(status_code=404, detail="联系人不存在")
    return {"message": "更新成功"}


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int):
    """删除联系人"""
    from services.database import get_conn
    with get_conn() as conn:
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    return {"message": "删除成功"}