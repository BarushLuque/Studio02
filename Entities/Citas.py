from sqlalchemy import Column, Integer, DateTime, Enum, Text, String, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base

class Cita(Base):
    __tablename__ = 'citas'

    id_cita = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'))
    fecha = Column(DateTime, nullable=False)
    estado = Column(Enum('agendada', 'completada', 'cancelada'), default='agendada')
    notas = Column(Text)

    cliente = relationship("Cliente", back_populates="citas")
    detalles = relationship("DetalleCita", back_populates="cita")
