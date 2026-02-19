"""Base Repository para CRUD genérico e métodos comuns."""
from typing import Type, TypeVar, Generic, List, Optional
from sqlalchemy.orm import Session
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: dict) -> ModelType:
        # Filtra campos que não existem no modelo
        valid_fields = {c.key for c in self.model.__table__.columns}
        filtered_data = {k: v for k, v in obj_in.items() if k in valid_fields}
        
        db_obj = self.model(**filtered_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: ModelType, obj_in: dict
    ) -> ModelType:
        # Filtra campos que não existem no modelo
        valid_fields = {c.key for c in self.model.__table__.columns}
        
        for field, value in obj_in.items():
            if field in valid_fields:
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> Optional[ModelType]:
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
