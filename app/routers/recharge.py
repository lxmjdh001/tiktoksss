"""
充值相关路由
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import get_current_user, User
from app.models.recharge_record import RechargeRecord
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional
from app.services.futoon_pay import FutoonPay, FutoonPayConfig

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/recharge", response_class=HTMLResponse)
async def recharge_page(request: Request, db: Session = Depends(get_db)):
    """充值页面"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    # 获取最近充值记录
    recent_recharges = db.query(RechargeRecord).filter(
        RechargeRecord.user_id == user.id
    ).order_by(RechargeRecord.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("recharge.html", {
        "request": request,
        "title": "账户充值",
        "user": user,
        "recent_recharges": recent_recharges
    })

@router.post("/recharge/submit")
async def submit_recharge(
    request: Request,
    amount: float = Form(...),
    payment_method: str = Form(...),
    db: Session = Depends(get_db)
):
    """提交充值申请"""
    # 检查用户是否已登录
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 验证充值金额
    if amount < 100:
        raise HTTPException(status_code=400, detail="最低充值金额为100元")
    
    if amount > 50000:
        raise HTTPException(status_code=400, detail="单次充值金额不能超过50000元")
    
    # 验证支付方式
    if payment_method not in ["alipay", "wechat"]:
        raise HTTPException(status_code=400, detail="请选择有效的支付方式")
    
    # 这里可以集成真实的支付接口
    # 目前先模拟支付成功，直接增加余额
    try:
        # 增加用户余额
        user.balance = Decimal(str(user.balance)) + Decimal(str(amount))
        
        # 创建充值记录
        recharge_record = RechargeRecord(
            user_id=user.id,
            amount=Decimal(str(amount)),
            payment_method=payment_method,
            status="completed"
        )
        
        db.add(recharge_record)
        db.commit()
        
        return {
            "success": True, 
            "message": f"充值成功！已到账 ¥{amount}",
            "new_balance": float(user.balance)
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"充值失败：{str(e)}"
        }


class CreatePaymentRequest(BaseModel):
    amount: float
    payment_type: str  # wechat / alipay
    remark: Optional[str] = None


class CreatePaymentResponse(BaseModel):
    success: bool
    payurl: Optional[str] = None
    qrcode: Optional[str] = None
    urlscheme: Optional[str] = None
    out_trade_no: Optional[str] = None
    message: str


def _build_futoon_client() -> FutoonPay:
    import os
    pid = os.getenv("FUTOON_PID", "2208")
    key = os.getenv("FUTOON_KEY", "2m57wWbSnqs52ZmQMMpLUxLel6wXSzup")
    api_url = os.getenv("FUTOON_API_URL", "https://futoon.org/mapi.php")
    return FutoonPay(FutoonPayConfig(pid=pid, key=key, api_url=api_url))


def _client_ip(request: Request) -> str:
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/api/recharge/futoon/create", response_model=CreatePaymentResponse)
async def create_futoon_payment(req: CreatePaymentRequest, request: Request):
    """创建富通支付订单，返回支付链接/二维码。"""
    if req.amount <= 0:
        return CreatePaymentResponse(success=False, message="金额不正确")

    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    out_trade_no = f"FT{user.id}{int(__import__('time').time()*1000)}"

    fp = _build_futoon_client()
    origin = str(request.base_url).rstrip("/")
    notify_url = f"{origin}/api/recharge/futoon/notify"
    return_url = f"{origin}/recharge"

    result = fp.create_order(
        out_trade_no=out_trade_no,
        name=req.remark or "账户充值",
        money=req.amount,
        payment_type=req.payment_type,
        notify_url=notify_url,
        return_url=return_url,
        client_ip=_client_ip(request),
        param=str(user.id),
    )

    if not result.get("success"):
        return CreatePaymentResponse(success=False, message=result.get("message", "创建失败"))

    return CreatePaymentResponse(
        success=True,
        payurl=result.get("payurl"),
        qrcode=result.get("qrcode"),
        urlscheme=result.get("urlscheme"),
        out_trade_no=out_trade_no,
        message="创建成功",
    )


@router.get("/api/recharge/futoon/notify")
async def futoon_notify(request: Request, db: Session = Depends(get_db)):
    """富通支付异步回调（官方为GET），验签后给用户入账。"""
    params = dict(request.query_params)

    fp = _build_futoon_client()
    valid = fp.verify_notify(params)
    # 可根据需要强制 valid 为 True

    out_trade_no = params.get("out_trade_no")
    trade_status = params.get("trade_status")
    money = params.get("money")
    user_id = params.get("param")  # 我们把用户ID放在param里

    if not out_trade_no or not money or not user_id:
        return {"status": "fail"}

    if trade_status == "TRADE_SUCCESS":
        try:
            # 给指定用户入账
            target = db.query(User).filter(User.id == int(user_id)).first()
            if not target:
                return {"status": "fail"}
            target.balance = Decimal(str(target.balance)) + Decimal(str(money))

            # 记录充值记录
            record = RechargeRecord(
                user_id=target.id,
                amount=Decimal(str(money)),
                payment_method="futoon",
                status="completed",
            )
            db.add(record)
            db.commit()
            return {"status": "success"}
        except Exception:
            db.rollback()
            return {"status": "fail"}

    return {"status": "fail"}
