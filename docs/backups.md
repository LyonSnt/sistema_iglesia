# Backups

## Objetivo

Proteger datos criticos: PostgreSQL y archivos subidos en `media`.

## Politica inicial

- Backup diario de PostgreSQL.
- Backup semanal de `media`.
- Retencion configurable segun espacio disponible.
- Restauracion documentada y probada.

## PostgreSQL

Comando esperado dentro del entorno Docker:

```bash
docker compose exec db pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc > backups/ecclesia.dump
```

## Media

Los archivos subidos viven en el volumen `media_volume` y se montan en `/app/media`.

## Pendiente

- Crear `scripts/backup_db.sh`.
- Crear `scripts/restore_db.sh`.
- Crear `scripts/backup_media.sh`.
- Definir retencion.
