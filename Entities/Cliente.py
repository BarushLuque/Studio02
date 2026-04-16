from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from DAO.db import Base

class Cliente(Base):
    __tablename__ = 'clientes'

    id_cliente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    fecha_registro = Column(DateTime, server_default=func.current_timestamp())

    citas = relationship("Cita", back_populates="cliente")