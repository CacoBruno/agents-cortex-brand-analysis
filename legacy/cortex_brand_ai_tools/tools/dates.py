from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  

def get_date_range(days_back: int = 7, tz: str = "America/Sao_Paulo"):
    """
    Retorna duas strings:
      • start_date – data de hoje menos `days_back` dias
      • end_date   – data de hoje
    As datas vêm no formato 'AAAA-MM-DD'.
    
    Parameters
    ----------
    days_back : int
        Quantos dias voltar no tempo. Padrão = 7.
    tz : str
        Timezone em formato IANA/Olson. Padrão = 'America/Sao_Paulo'.
    
    Returns
    -------
    tuple[str, str]
        (start_date, end_date)
    """
    today = datetime.now(ZoneInfo(tz)).date()
    start_date = today - timedelta(days=days_back)
    
    # Converte para string ISO-8601
    return start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")



from datetime import date, timedelta

def last_weekday(target_weekday: str, ref_date: date | None = None) -> date:
    """
    Retorna a última data do dia da semana informado.
    O próprio dia também vale.

    Ex:
        last_weekday("monday") -> última segunda (ou hoje, se hoje for segunda)

    target_weekday: monday, tuesday, wednesday, thursday, friday, saturday, sunday
    ref_date: data de referência (default = hoje)
    """

    if ref_date is None:
        ref_date = date.today()

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    target_weekday = target_weekday.lower()

    if target_weekday not in weekdays:
        raise ValueError(f"Dia inválido: {target_weekday}")

    target = weekdays[target_weekday]
    today = ref_date.weekday()

    # diferença para trás (0 se for o mesmo dia)
    delta_days = (today - target) % 7
    anchor_date = ref_date - timedelta(days=delta_days)
    return anchor_date.isoformat()


from datetime import date, timedelta

def last_weekday_weeks_ago(
    target_weekday: str,
    weeks_back: int = 2,
    ref_date: date | None = None
) -> str:
    """
    Retorna a data da última ocorrência do dia da semana informado,
    voltando N semanas.

    Ex:
        last_weekday_weeks_ago("monday", 2)
        -> segunda-feira de duas semanas atrás

    target_weekday: monday, tuesday, wednesday, thursday,
                    friday, saturday, sunday
    weeks_back: número de semanas para voltar (default=2)
    ref_date: data de referência (default = hoje)
    """

    if ref_date is None:
        ref_date = date.today()

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    target_weekday = target_weekday.lower()

    if target_weekday not in weekdays:
        raise ValueError(f"Dia inválido: {target_weekday}")

    target = weekdays[target_weekday]
    today = ref_date.weekday()

    # última ocorrência do weekday
    delta_days = (today - target) % 7
    anchor_date = ref_date - timedelta(days=delta_days)

    # volta N semanas
    result_date = anchor_date - timedelta(weeks=weeks_back)

    return result_date.isoformat()