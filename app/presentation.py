from __future__ import annotations

from datetime import datetime
from typing import Any


SUPPORTED_LANGUAGES = ("en", "fi", "sv")
DEFAULT_LANGUAGE = "en"

COPY: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Pikkukoski Water Quality",
        "hero_eyebrow": "Predicted water quality",
        "hero_summary": "A fast reading of recent rain, model output, and the latest official sample for Pikkukoski.",
        "predicted_at": "Predicted at {timestamp}.",
        "bad_water_probability": "Bad-water probability {value}%.",
        "no_prediction_yet": "No prediction yet",
        "run_jobs_first": "Run the ingestion, training, and prediction jobs first.",
        "disclaimer": "This is a model estimate based on recent rainfall and historical measurements. It is not an official bathing advisory.",
        "predicted_enterococci": "Predicted enterococci",
        "predicted_ecoli": "Predicted E. coli",
        "recent_rainfall": "Recent rainfall",
        "rainfall_caption": "Hourly rain observations from Kumpula. Bars make short bursts and dry periods easier to read than a list.",
        "prediction_history": "Prediction history",
        "history_caption": "Recent model outputs shown as bad-water probability. Dots are colored by predicted class.",
        "last_24h_total": "Last 24 h total",
        "latest_probability": "Latest probability",
        "language": "Language",
        "thresholds": "Bacteria reference thresholds",
        "thresholds_caption": "Official inland bathing-water action thresholds are shown as reference. The lower watch band is a conservative UI aid for risk-averse swimmers, not an official limit.",
        "watch_band": "Conservative watch line",
        "action_threshold": "Action threshold",
        "threshold_legend": "Reference lines",
        "predicted_marker": "Prediction",
        "official_marker": "Official sample",
        "no_official_sample": "No official sample yet",
        "official_measurement_date": "Official sample date",
        "model_signal": "Model signal",
        "confidence_explainer": "Higher values mean the model sees a greater chance of poor water quality.",
        "elevated_risk_threshold_label": "Elevated-risk threshold",
        "poor_threshold_label": "Poor-water threshold",
        "chart_empty": "Not enough data yet.",
        "threshold_source_note": "Reference values follow Helsinki inland bathing-water sample thresholds and the EU Bathing Water Directive classification framework.",
        "watch_band_note": "Set here at 50% of the inland action threshold for added caution.",
        "visible_scale_max": "Scale max",
        "coastal_note": "For coastal waters, official action thresholds are lower: 200 for enterococci and 500 for E. coli.",
        "no_rain_observed": "No rain observed in this window.",
    },
    "fi": {
        "page_title": "Pikkukosken uimaveden laatu",
        "hero_eyebrow": "Ennustettu vedenlaatu",
        "hero_summary": "Nopea näkymä viimeaikaiseen sateeseen, mallin arvioon ja Pikkukosken uusimpaan viralliseen näytteeseen.",
        "predicted_at": "Ennuste tehty {timestamp}.",
        "bad_water_probability": "Huonon veden todennäköisyys {value} %.",
        "no_prediction_yet": "Ennustetta ei vielä ole",
        "run_jobs_first": "Aja ensin datan haku-, koulutus- ja ennusteajot.",
        "disclaimer": "Tämä on mallin arvio viimeaikaisen sateen ja historiallisten mittausten perusteella. Se ei ole virallinen uimavesisuositus.",
        "predicted_enterococci": "Ennustetut enterokokit",
        "predicted_ecoli": "Ennustettu E. coli",
        "recent_rainfall": "Viimeaikainen sade",
        "rainfall_caption": "Kumpulan tuntisadehavainnot. Pylväät näyttävät kuurot ja kuivat jaksot listaa selvemmin.",
        "prediction_history": "Ennustehistoria",
        "history_caption": "Viimeaikaiset mallitulokset huonon veden todennäköisyytenä. Pisteiden väri kertoo ennustetun luokan.",
        "last_24h_total": "Viimeiset 24 h yhteensä",
        "latest_probability": "Uusin todennäköisyys",
        "language": "Kieli",
        "thresholds": "Bakteerien viitearvot",
        "thresholds_caption": "Viralliset sisämaan uimavesien toimenpiderajat näytetään vertailuna. Alempi tarkkailuvyöhyke on varovainen käyttöliittymän apuarvo, ei virallinen raja.",
        "watch_band": "Varovainen tarkkailuraja",
        "action_threshold": "Toimenpideraja",
        "threshold_legend": "Viiterajat",
        "predicted_marker": "Ennuste",
        "official_marker": "Virallinen näyte",
        "no_official_sample": "Virallista näytettä ei vielä ole",
        "official_measurement_date": "Virallisen näytteen päivä",
        "model_signal": "Mallin signaali",
        "confidence_explainer": "Suurempi arvo tarkoittaa, että malli arvioi huonon veden todennäköisyyden suuremmaksi.",
        "elevated_risk_threshold_label": "Kohonneen riskin raja",
        "poor_threshold_label": "Huonon veden raja",
        "chart_empty": "Dataa ei vielä ole riittävästi.",
        "threshold_source_note": "Viitearvot perustuvat Helsingin sisämaan uimavesien näytekohtaisiin toimenpiderajoihin ja EU:n uimavesidirektiivin luokitteluun.",
        "watch_band_note": "Asetettu tässä 50 prosenttiin sisämaan toimenpiderajasta lisävarovaisuuden vuoksi.",
        "visible_scale_max": "Asteikon maksimi",
        "coastal_note": "Rannikkovesissä viralliset toimenpiderajat ovat matalammat: 200 enterokokeille ja 500 E. colille.",
        "no_rain_observed": "Tällä aikavälillä ei ole havaittu sadetta.",
    },
    "sv": {
        "page_title": "Vattenkvaliteten i Lillforsen",
        "hero_eyebrow": "Prognostiserad vattenkvalitet",
        "hero_summary": "En snabb läsning av nyligt regn, modellutfall och det senaste officiella provet för Pikkukoski.",
        "predicted_at": "Prognosen gjordes {timestamp}.",
        "bad_water_probability": "Sannolikhet för dåligt vatten {value} %.",
        "no_prediction_yet": "Ingen prognos ännu",
        "run_jobs_first": "Kör först jobben för datainhämtning, träning och prognos.",
        "disclaimer": "Detta är en modelluppskattning baserad på nyligt regn och historiska mätningar. Den är inte en officiell badrekommendation.",
        "predicted_enterococci": "Prognostiserade enterokocker",
        "predicted_ecoli": "Prognostiserad E. coli",
        "recent_rainfall": "Nyligt regn",
        "rainfall_caption": "Timvisa regnobservationer från Gumtäkt. Staplar gör skurar och torra perioder lättare att läsa än en lista.",
        "prediction_history": "Prognoshistorik",
        "history_caption": "Senaste modellutfall visade som sannolikhet för dåligt vatten. Punkterna färgsätts enligt prognostiserad klass.",
        "last_24h_total": "Senaste 24 h totalt",
        "latest_probability": "Senaste sannolikhet",
        "language": "Språk",
        "thresholds": "Referensgränser för bakterier",
        "thresholds_caption": "Officiella åtgärdsgränser för badvatten i inland visas som referens. Den lägre observationszonen är ett försiktigt gränssnittshjälpmedel, inte en officiell gräns.",
        "watch_band": "Försiktig observationslinje",
        "action_threshold": "Åtgärdsgräns",
        "threshold_legend": "Referenslinjer",
        "predicted_marker": "Prognos",
        "official_marker": "Officiellt prov",
        "no_official_sample": "Inget officiellt prov ännu",
        "official_measurement_date": "Datum för officiellt prov",
        "model_signal": "Modellsignal",
        "confidence_explainer": "Högre värden betyder att modellen ser större sannolikhet för dålig vattenkvalitet.",
        "elevated_risk_threshold_label": "Tröskel för förhöjd risk",
        "poor_threshold_label": "Tröskel för dåligt vatten",
        "chart_empty": "Det finns inte tillräckligt med data ännu.",
        "threshold_source_note": "Referensvärdena följer Helsingfors åtgärdsgränser för enskilda inlandsvattenprov och EU:s badvattendirektiv.",
        "watch_band_note": "Den är här satt till 50 procent av inlandets åtgärdsgräns för extra försiktighet.",
        "visible_scale_max": "Skalans max",
        "coastal_note": "För kustvatten är de officiella åtgärdsgränserna lägre: 200 för enterokocker och 500 för E. coli.",
        "no_rain_observed": "Ingen nederbörd observerades under det här intervallet.",
    },
}

STATUS_LABELS = {
    "en": {"good": "Good", "elevated-risk": "Elevated risk", "poor": "Poor"},
    "fi": {"good": "Hyvä", "elevated-risk": "Kohonnut riski", "poor": "Huono"},
    "sv": {"good": "Bra", "elevated-risk": "Förhöjd risk", "poor": "Dålig"},
}

LANGUAGE_LABELS = {
    "en": {"en": "English", "fi": "Suomi", "sv": "Svenska"},
    "fi": {"en": "English", "fi": "Suomi", "sv": "Svenska"},
    "sv": {"en": "English", "fi": "Suomi", "sv": "Svenska"},
}

METRIC_REFERENCE_LIMITS = {
    "enterococci": {
        "unit": "cfu/100 ml",
        "watch_threshold": 200,
        "action_threshold": 400,
        "display_max": 800,
    },
    "ecoli": {
        "unit": "cfu/100 ml",
        "watch_threshold": 500,
        "action_threshold": 1000,
        "display_max": 2500,
    },
}


def resolve_language(lang: str | None) -> str:
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def copy_for_language(lang: str) -> dict[str, str]:
    return COPY[resolve_language(lang)]


def language_options(active_lang: str) -> list[dict[str, str | bool]]:
    lang = resolve_language(active_lang)
    return [
        {"code": code, "label": LANGUAGE_LABELS[lang][code], "active": code == lang}
        for code in SUPPORTED_LANGUAGES
    ]


def localize_status(lang: str, status: str | None) -> str:
    if not status:
        return ""
    resolved = resolve_language(lang)
    return STATUS_LABELS[resolved].get(status, status.replace("-", " ").title())


def format_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d %H:%M")


def format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%Y-%m-%d")


def _chart_dimensions(width: int = 640, height: int = 220, padding: int = 24) -> dict[str, int]:
    return {"width": width, "height": height, "padding": padding}


def build_rain_chart(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = _chart_dimensions()
    if not rows:
        return {**dimensions, "bars": [], "has_data": False, "y_ticks": [], "latest": None, "summary_total": 0.0}

    width = dimensions["width"]
    height = dimensions["height"]
    padding = dimensions["padding"]
    inner_width = width - padding * 2
    inner_height = height - padding * 2
    values = [float(row["rain_mm"]) for row in rows]
    max_value = max(values) or 1.0
    step = inner_width / max(len(rows), 1)
    bar_width = max(step * 0.58, 6.0)
    bars = []
    for index, row in enumerate(rows):
        value = float(row["rain_mm"])
        bar_height = 0.0 if max_value == 0 else (value / max_value) * inner_height
        x = padding + index * step + (step - bar_width) / 2
        y = height - padding - bar_height
        bars.append(
            {
                "x": round(x, 2),
                "y": round(y, 2),
                "width": round(bar_width, 2),
                "height": round(bar_height, 2),
                "value": value,
                "label": format_timestamp(row["observed_at"]) or row["observed_at"],
            }
        )

    all_zero = max(values) == 0
    y_ticks = [0.0, round(max_value / 2, 1), round(max_value, 1)]
    return {
        **dimensions,
        "bars": bars,
        "has_data": True,
        "all_zero": all_zero,
        "y_ticks": y_ticks,
        "latest": values[-1],
        "summary_total": round(sum(values[-4:]), 2),
    }


def build_history_chart(rows: list[dict[str, Any]], lang: str) -> dict[str, Any]:
    dimensions = _chart_dimensions()
    if not rows:
        return {
            **dimensions,
            "has_data": False,
            "line_path": "",
            "area_path": "",
            "dots": [],
            "y_ticks": [0, 25, 50, 75, 100],
            "latest_probability": None,
        }

    ordered_rows = list(reversed(rows))
    width = dimensions["width"]
    height = dimensions["height"]
    padding = dimensions["padding"]
    inner_width = width - padding * 2
    inner_height = height - padding * 2
    step = inner_width / max(len(ordered_rows) - 1, 1)
    coords: list[tuple[float, float]] = []
    dots = []
    for index, row in enumerate(ordered_rows):
        probability = round(float(row["quality_probability_bad"]) * 100, 1)
        x = padding + index * step
        y = padding + (100 - probability) / 100 * inner_height
        coords.append((x, y))
        dots.append(
            {
                "x": round(x, 2),
                "y": round(y, 2),
                "probability": probability,
                "status": row["quality_label_predicted"],
                "status_label": localize_status(lang, row["quality_label_predicted"]),
                "label": format_timestamp(row["predicted_at"]) or row["predicted_at"],
            }
        )

    first_x, first_y = coords[0]
    line_path = "M " + " L ".join(f"{round(x, 2)} {round(y, 2)}" for x, y in coords)
    area_path = (
        f"M {round(first_x, 2)} {height - padding} "
        + "L "
        + " L ".join(f"{round(x, 2)} {round(y, 2)}" for x, y in coords)
        + f" L {round(coords[-1][0], 2)} {height - padding} Z"
    )
    return {
        **dimensions,
        "has_data": True,
        "line_path": line_path,
        "area_path": area_path,
        "dots": dots,
        "y_ticks": [0, 25, 50, 75, 100],
        "latest_probability": dots[-1]["probability"],
    }


def build_threshold_gauge(metric_key: str, predicted_value: float | int | None, official_value: Any) -> dict[str, Any]:
    config = METRIC_REFERENCE_LIMITS[metric_key]
    predicted = None if predicted_value is None else float(predicted_value)
    official = None if official_value in (None, "", "n/a") else float(official_value)
    upper_bound = max(
        float(config["display_max"]),
        predicted or 0.0,
        official or 0.0,
        config["watch_threshold"],
    )

    def to_pct(value: float) -> float:
        return min(100.0, round(value / upper_bound * 100, 2))

    return {
        "unit": config["unit"],
        "watch_threshold": config["watch_threshold"],
        "action_threshold": config["action_threshold"],
        "watch_pct": to_pct(config["watch_threshold"]),
        "action_pct": to_pct(config["action_threshold"]),
        "predicted_value": predicted,
        "official_value": official,
        "predicted_pct": None if predicted is None else to_pct(predicted),
        "official_pct": None if official is None else to_pct(official),
        "max_value": round(upper_bound),
    }


def build_probability_thresholds(elevated_risk_threshold: float, poor_threshold: float) -> dict[str, float]:
    return {
        "elevated_risk_threshold": elevated_risk_threshold,
        "poor_threshold": poor_threshold,
        "elevated_risk_pct": round(elevated_risk_threshold * 100, 1),
        "poor_pct": round(poor_threshold * 100, 1),
    }
