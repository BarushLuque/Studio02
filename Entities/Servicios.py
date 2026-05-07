from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from DAO.db import Base


class Servicio(Base):
    __tablename__ = 'servicios'

    id_servicio = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_categoria = Column(Integer, ForeignKey('categorias_servicio.id_categoria'))
    nombre_servicio = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    duracion_minutos = Column(Integer, nullable=False)

    # Relación: cada servicio pertenece a una categoría
    categoria = relationship("CategoriaServicio", back_populates="servicios")

    # Relación: un servicio puede aparecer en muchos detalles de cita
    detalles = relationship("DetalleCita", back_populates="servicio")
