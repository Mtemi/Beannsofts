from app.src import db

class BaseClass():
    _abstract__ = True

    @classmethod
    def save_to_db(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.commit()

    @classmethod
    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
