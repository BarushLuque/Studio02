from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base
import enum

class EstadoCita(enum.Enum):
    pendiente = "pendiente"
    agendada = "agendada"
    completada = "completada"
    cancelada = "cancelada"
    no_asistio = "no_asistio"  

class Cita(Base):
    __tablename__ = 'citas'

    id_cita = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)

    # Fechas según el dump oficial
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)

    estado = Column(Enum(EstadoCita), default=EstadoCita.agendada)
    notas = Column(Text)

    cliente = relationship("Cliente", back_populates="citas")
    detalles = relationship("DetalleCita", back_populates="cita", cascade="all, delete-orphan")
