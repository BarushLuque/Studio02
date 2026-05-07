from sqlalchemy import Column, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base
import enum

class EstadoCita(enum.Enum):
    agendada = "agendada"
    completada = "completada"
    cancelada = "cancelada"

class Cita(Base):
    __tablename__ = 'citas'

    id_cita = Column(Integer, primary_key=True, index=True)
    # Se agregó nullable=False para asegurar integridad
    id_cliente = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    fecha = Column(DateTime, nullable=False)
    # Se utiliza el Enum definido arriba para evitar errores de escritura
    estado = Column(Enum(EstadoCita), default=EstadoCita.agendada)
    notas = Column(Text)

    cliente = relationship("Cliente", back_populates="citas")
    detalles = relationship("DetalleCita", back_populates="cita")