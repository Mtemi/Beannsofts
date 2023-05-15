from app.src.models import SmartOrdersModel
from app.src import db
from app import app
import datetime

ctx = app.app_context()


def modifyOrder(order_id,status,reason, executed_on, modified_on):
    
    try:
        ctx.push()
        db.session.query(SmartOrdersModel).filter_by(id=order_id).update({'status':status,'modified_on':modified_on, 'executed_on':executed_on, 'change_reason':reason})
        db.session.commit()
        ctx.pop()
        return {"status":True, "message":"success"}
    except Exception as e:
        return {"status":False, "message":str(e)}

def cancelOrder(order_id):
    try:
        temp_order_data = db.session.query(SmartOrdersModel).filter_by(id=order_id).first()
        resp =modifyOrder(order_id, status="cancelled", reason="user intiated cancel", executed_on=datetime.datetime.utcnow(), modified_on=datetime.datetime.utcnow())
        if resp['status']==True:
            return {"status":True, "message":"success", "task_id":temp_order_data.task_id}
        else:
            return resp
    except Exception as e:
        return {"status":False, "message":str(e)}

def updateTaskId(order_id, task_id):
    try:
        db.session.query(SmartOrdersModel).filter_by(id=order_id).update({"task_id":task_id})
        db.session.commit()

        return {"status":True, "message":"success"}
    except Exception as e:
        return {"status":False, "message":str(e)}

