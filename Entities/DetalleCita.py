from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base


class DetalleCita(Base):
    __tablename__ = 'detalle_cita'

    id_detalle = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_cita = Column(Integer, ForeignKey('citas.id_cita'), nullable=False)
    id_servicio = Column(Integer, ForeignKey('servicios.id_servicio'), nullable=False)
    precio_aplicado = Column(Numeric(10, 2), nullable=False)

    # Relación: cada detalle pertenece a una cita
    cita     = relationship("Cita", back_populates="detalles")

    # Relación: cada detalle referencia un servicio
    servicio = relationship("Servicio", back_populates="detalles")
