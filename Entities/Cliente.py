from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from DAO.db import Base

class Cliente(Base):
    __tablename__ = 'clientes'

    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)


    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20))
    email = Column(String(255), unique=True)

    notas = Column(Text)

    fecha_registro = Column(DateTime, server_default=func.current_timestamp())

    # Relación: un cliente puede tener muchas citas
    citas = relationship("Cita", back_populates="cliente")
