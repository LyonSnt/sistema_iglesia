def usuario_es_nacional(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return bool(getattr(user, "is_superuser", False) or getattr(user, "es_usuario_nacional", False))


def obtener_iglesia_usuario(user):
    if not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "iglesia", None)


def filtrar_queryset_por_iglesia(queryset, user, campo_iglesia="iglesia"):
    if usuario_es_nacional(user):
        return queryset

    iglesia = obtener_iglesia_usuario(user)
    if iglesia is None:
        return queryset.none()

    return queryset.filter(**{campo_iglesia: iglesia})


class IglesiaQuerysetMixin:
    campo_iglesia = "iglesia"

    def filtrar_por_usuario(self, queryset, user):
        return filtrar_queryset_por_iglesia(queryset, user, self.campo_iglesia)
