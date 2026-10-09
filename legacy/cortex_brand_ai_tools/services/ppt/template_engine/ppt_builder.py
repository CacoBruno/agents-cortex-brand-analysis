import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_CONNECTOR, MSO_AUTO_SHAPE_TYPE

from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR

def _normalize_pp_align(value, default=PP_ALIGN.LEFT):
    """
    Aceita:
      - enum PP_ALIGN
      - int (ex.: 1, 2, 3...)
      - string "CENTER (2)", "LEFT (1)", "RIGHT (3)", etc.
      - string simples "CENTER", "LEFT", ...
    """
    if value is None:
        return default

    # já é enum/int utilizável
    try:
        if isinstance(value, int):
            return value
    except:
        pass

    # string
    if isinstance(value, str):
        v = value.strip().upper()

        # extrai nome antes do "(2)"
        if "(" in v:
            v = v.split("(")[0].strip()

        mapping = {
            "LEFT": PP_ALIGN.LEFT,
            "CENTER": PP_ALIGN.CENTER,
            "RIGHT": PP_ALIGN.RIGHT,
            "JUSTIFY": PP_ALIGN.JUSTIFY,
            "DISTRIBUTE": getattr(PP_ALIGN, "DISTRIBUTE", default),
            "THAI_DISTRIBUTE": getattr(PP_ALIGN, "THAI_DISTRIBUTE", default),
            "JUSTIFY_LOW": getattr(PP_ALIGN, "JUSTIFY_LOW", default),
        }
        return mapping.get(v, default)

    return default


def _normalize_vertical_anchor(value, default=None):
    """
    Aceita:
      - string "BOTTOM (4)", "TOP (1)", "MIDDLE (3)"
      - string simples "BOTTOM", "TOP", "MIDDLE"
    """
    if value is None:
        return default

    if isinstance(value, str):
        v = value.strip().upper()
        if "(" in v:
            v = v.split("(")[0].strip()

        mapping = {
            "TOP": MSO_VERTICAL_ANCHOR.TOP,
            "MIDDLE": MSO_VERTICAL_ANCHOR.MIDDLE,
            "BOTTOM": MSO_VERTICAL_ANCHOR.BOTTOM,
        }
        return mapping.get(v, default)

    return default

##############################################
#   SUPORTE A CORES (RGB + THEME COLORS)
##############################################

HEX_COLOR_RE = re.compile(r'^[0-9a-fA-F]{6}$')

def parse_color(color_info):
    """
    Converte:
      - "AE0029"
      - {"type":"rgb","value":"AE0029"}
      - {"type":"theme","name":"ACCENT_4","index":8}
    """
    if color_info is None:
        return None

    # string hex antiga
    if isinstance(color_info, str) and HEX_COLOR_RE.match(color_info):
        return {"mode": "rgb", "value": RGBColor.from_string(color_info)}

    # formato estruturado
    if isinstance(color_info, dict):
        if color_info.get("type") == "rgb":
            return {"mode": "rgb", "value": RGBColor.from_string(color_info["value"])}

        if color_info.get("type") == "theme":
            try:
                theme_enum = getattr(MSO_THEME_COLOR, color_info["name"])
                return {"mode": "theme", "value": theme_enum}
            except:
                return None

    return None


##############################################
#   PARÁGRAFOS E TEXT ROLE
##############################################

def apply_paragraph_spacing(p, pjson):
    """Aplica espaçamento compatível com qualquer versão do python-pptx."""
    if pjson.get("line_spacing") is not None:
        try:
            p.line_spacing = pjson["line_spacing"]
        except:
            pass

    if pjson.get("line_spacing_rule"):
        try:
            p.line_spacing_rule = pjson["line_spacing_rule"]
        except:
            pass

    if pjson.get("space_before") is not None:
        try:
            p.space_before = Pt(pjson["space_before"])
        except:
            pass

    if pjson.get("space_after") is not None:
        try:
            p.space_after = Pt(pjson["space_after"])
        except:
            pass


def apply_text_role_defaults(run, text_role):
    """Aplica tamanho padrão quando o JSON não trouxe tamanho."""
    if run.font.size:
        return

    if text_role == "title":
        run.font.size = Pt(40)
    elif text_role == "subtitle":
        run.font.size = Pt(28)
    elif text_role == "body":
        run.font.size = Pt(18)
    elif text_role == "small_text":
        run.font.size = Pt(12)


##############################################
#   SLIDE BACKGROUND
##############################################

def set_slide_background(slide, color_info):
    """
    Se color_info = None -> transparente.
    Caso contrário -> aplica RGB ou theme.
    """
    if color_info is None:
        try:
            slide.background.fill.background()
        except:
            pass
        return

    col = parse_color(color_info)
    if not col:
        return

    fill = slide.background.fill
    fill.solid()

    if col["mode"] == "rgb":
        fill.fore_color.rgb = col["value"]
    else:
        fill.fore_color.theme_color = col["value"]


##############################################
#   TEXTBOX / PLACEHOLDER
##############################################

def build_textbox(slide, element):

    left   = element["position"]["left"]
    top    = element["position"]["top"]
    width  = element["position"]["width"]
    height = element["position"]["height"]

    shape = slide.shapes.add_textbox(left, top, width, height)

    # ---------------- BACKGROUND ----------------
    bg = element.get("placeholder_background_color")

    if bg is None:
        try:
            shape.fill.background()
        except:
            pass
    else:
        try:
            fill = shape.fill
            fill.solid()
            col = parse_color(bg)
            if col:
                if col["mode"] == "rgb":
                    fill.fore_color.rgb = col["value"]
                else:
                    fill.fore_color.theme_color = col["value"]
        except:
            pass

    text_role = element.get("text_role")

    # ---------------- TEXTO ----------------
    tf = shape.text_frame
    tf.clear()

    first = True
    for para in element.get("text", []):
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()

        p.alignment = _normalize_pp_align(para.get("alignment"), PP_ALIGN.LEFT)

        # runs
        for rjson in para["runs"]:
            run = p.add_run()
            run.text = rjson["text"]

            if rjson.get("font_name"):
                run.font.name = rjson["font_name"]

            if rjson.get("font_size"):
                run.font.size = Pt(rjson["font_size"])
            else:
                apply_text_role_defaults(run, text_role)

            run.font.bold = rjson.get("bold")
            run.font.italic = rjson.get("italic")
            run.font.underline = rjson.get("underline")

            col = parse_color(rjson.get("color"))
            if col:
                if col["mode"] == "rgb":
                    run.font.color.rgb = col["value"]
                else:
                    run.font.color.theme_color = col["value"]

        apply_paragraph_spacing(p, para)

    # remover sombra
    try:
        shape.shadow.inherit = False
        shape.shadow.visible = False
    except:
        pass

    return shape


##############################################
#   PICTURE
##############################################

def build_picture(slide, element):
    img = element["image"]["path"]

    left   = element["position"]["left"]
    top    = element["position"]["top"]
    width  = element["position"]["width"]
    height = element["position"]["height"]

    shape = slide.shapes.add_picture(img, left, top, width, height)

    try:
        shape.shadow.inherit = False
        shape.shadow.visible = False
    except:
        pass

    return shape


##############################################
#   LINE
##############################################
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.util import Emu

# opcionais (se quiser cap/join)
try:
    from pptx.enum.dml import MSO_LINE_CAP, MSO_LINE_JOIN_STYLE
except Exception:
    MSO_LINE_CAP = None
    MSO_LINE_JOIN_STYLE = None


def build_line(slide, element):
    pos  = element["position"]
    info = element.get("shape_info", {}) or {}

    left   = int(pos.get("left", 0))
    top    = int(pos.get("top", 0))
    width  = int(pos.get("width", 0))
    height = int(pos.get("height", 0))

    # -------------------------------------------------
    # Interpretar position como BOUNDING BOX (inspector)
    # -------------------------------------------------
    # Define orientação por proporção (mais robusto que width==0)
    if width == 0 and height == 0:
        # nada pra desenhar
        return None

    if width == 0 and height > 0:
        # vertical (degenerado)
        x1 = x2 = left
        y1 = top
        y2 = top + height

    elif height == 0 and width > 0:
        # horizontal (degenerado)
        x1 = left
        y1 = y2 = top
        x2 = left + width

    else:
        # bounding box “real”
        if height > width:
            # vertical: x no meio do box
            x = left + width // 2
            x1, y1 = x, top
            x2, y2 = x, top + height
        else:
            # horizontal: y no meio do box
            y = top + height // 2
            x1, y1 = left, y
            x2, y2 = left + width, y

    # -------------------------------------------------
    # Cria connector
    # -------------------------------------------------
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        x1, y1, x2, y2
    )

    # -------------------------------------------------
    # Linha: fill sólido antes de aplicar cor/dash
    # -------------------------------------------------
    try:
        line.line.fill.solid()
    except Exception:
        pass

    # Cor
    col = parse_color(info.get("line_color"))
    if col:
        try:
            if col["mode"] == "rgb":
                line.line.color.rgb = col["value"]
            else:
                line.line.color.theme_color = col["value"]
        except Exception:
            pass

    # Espessura (python-pptx gosta de Length; Emu() deixa consistente)
    lw = info.get("line_width")
    if lw is not None:
        try:
            line.line.width = Emu(int(lw))
        except Exception:
            pass

    # Dash
    dash = info.get("line_dash")
    if dash:
        try:
            line.line.dash_style = getattr(MSO_LINE_DASH_STYLE, dash)
        except Exception:
            pass

    # Cap / Join (se existirem e se o python-pptx suportar na sua versão)
    cap = info.get("line_cap")
    if cap and MSO_LINE_CAP is not None:
        try:
            line.line.cap_style = getattr(MSO_LINE_CAP, cap)
        except Exception:
            pass

    join = info.get("line_join")
    if join and MSO_LINE_JOIN_STYLE is not None:
        try:
            line.line.join_style = getattr(MSO_LINE_JOIN_STYLE, join)
        except Exception:
            pass

    # Shadow off
    try:
        line.shadow.inherit = False
        line.shadow.visible = False
    except Exception:
        pass

    return line


##############################################
#   AUTOSHAPE
##############################################
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn


def _set_solid_fill_alpha(shape, transparency: float):
    """
    Força transparência do fill via XML (DrawingML).
    transparency: 0.0 (opaco) → 1.0 (totalmente transparente)
    No XML usamos <a:alpha val="..."> onde val = OPACIDADE * 100000
    """
    if transparency is None:
        return

    # clamp
    t = float(transparency)
    if t < 0: t = 0.0
    if t > 1: t = 1.0

    # alpha = opacidade (1 - transparência)
    alpha_val = int(round((1.0 - t) * 100000))

    spPr = shape._element.spPr  # <p:spPr>
    # remove <a:noFill> se existir
    noFill = spPr.find(qn("a:noFill"))
    if noFill is not None:
        spPr.remove(noFill)

    # garante <a:solidFill>
    solidFill = spPr.find(qn("a:solidFill"))
    if solidFill is None:
        solidFill = OxmlElement("a:solidFill")
        spPr.insert(0, solidFill)

    # procura o nó de cor: <a:srgbClr> OU <a:schemeClr>
    clr = solidFill.find(qn("a:srgbClr"))
    if clr is None:
        clr = solidFill.find(qn("a:schemeClr"))

    # se não existir, não tem onde colocar alpha
    if clr is None:
        return

    # remove alpha antigo
    old_alpha = clr.find(qn("a:alpha"))
    if old_alpha is not None:
        clr.remove(old_alpha)

    # cria novo alpha
    a = OxmlElement("a:alpha")
    a.set("val", str(alpha_val))
    clr.append(a)


def build_autoshape(slide, element):
    pos  = element.get("position", {})
    info = element.get("shape_info", {})

    # -------------------------------------------------
    # SHAPE
    # -------------------------------------------------
    shape_style = info.get("shape_style")
    if not shape_style:
        return None

    shape_name = shape_style.split("(")[0].strip()  # "OVAL (9)" → "OVAL"
    try:
        shape_enum = getattr(MSO_AUTO_SHAPE_TYPE, shape_name)
    except AttributeError:
        print(f"[WARN] AutoShape não reconhecido: {shape_name}")
        return None

    shape = slide.shapes.add_shape(
        shape_enum,
        pos.get("left", 0),
        pos.get("top", 0),
        pos.get("width", 0),
        pos.get("height", 0),
    )

    # -------------------------------------------------
    # FILL
    # -------------------------------------------------
    fill_color        = info.get("fill_color")
    fill_transparency = info.get("fill_transparency")

    if fill_color is None and fill_transparency is None:
        # sem fill → transparente real
        try:
            shape.fill.background()
        except:
            pass
    else:
        try:
            shape.fill.solid()

            # cor (RGB ou THEME)
            col = parse_color(fill_color)
            if col:
                if col["mode"] == "rgb":
                    shape.fill.fore_color.rgb = col["value"]
                else:
                    shape.fill.fore_color.theme_color = col["value"]

            # tentativa "normal" (às vezes não funciona)
            if fill_transparency is not None:
                try:
                    shape.fill.fore_color.transparency = float(fill_transparency)
                except:
                    pass

            # FORÇA no XML (funciona de verdade)
            if fill_transparency is not None:
                _set_solid_fill_alpha(shape, float(fill_transparency))

        except:
            pass

    # -------------------------------------------------
    # LINE
    # -------------------------------------------------
    line_color = info.get("line_color")
    line_width = info.get("line_width")

    if not line_color or not line_width or line_width == 0:
        try:
            shape.line.fill.background()
        except:
            pass
    else:
        try:
            col = parse_color(line_color)
            if col:
                if col["mode"] == "rgb":
                    shape.line.color.rgb = col["value"]
                else:
                    shape.line.color.theme_color = col["value"]
            shape.line.width = line_width
        except:
            pass

    # -------------------------------------------------
    # TEXT
    # -------------------------------------------------
    if "text" in element:
        tf = shape.text_frame
        tf.clear()

        for i, pjson in enumerate(element.get("text", [])):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = _normalize_pp_align(pjson.get("alignment"), PP_ALIGN.LEFT)

            for rjson in pjson.get("runs", []):
                run = p.add_run()
                run.text = rjson.get("text", "")

                if rjson.get("font_name"):
                    run.font.name = rjson["font_name"]
                if rjson.get("font_size"):
                    run.font.size = Pt(rjson["font_size"])

                run.font.bold      = rjson.get("bold")
                run.font.italic    = rjson.get("italic")
                run.font.underline = rjson.get("underline")

                col = parse_color(rjson.get("color"))
                if col:
                    if col["mode"] == "rgb":
                        run.font.color.rgb = col["value"]
                    else:
                        run.font.color.theme_color = col["value"]

            apply_paragraph_spacing(p, pjson)

    # -------------------------------------------------
    # SHADOW (desligar)
    # -------------------------------------------------
    try:
        shape.shadow.inherit = False
        shape.shadow.visible = False
    except:
        pass

    return shape

##############################################
#   TABLE
##############################################
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

def _normalize_cell_data(cdata, r=None, c=None):
    if isinstance(cdata, dict):
        return cdata

    if isinstance(cdata, list):
        if not cdata:
            return {}
        if len(cdata) == 1 and isinstance(cdata[0], dict):
            return cdata[0]

    pos = f"cells[{r}][{c}]" if r is not None and c is not None else "célula"
    raise ValueError(f"Estrutura inválida em {pos}: {type(cdata)} -> {cdata}")

def _rgb_value_to_rgbcolor(v):
    """
    Aceita:
      - "AE0029" (str HEX)
      - RGBColor(...)
    Retorna RGBColor ou None.
    """
    if v is None:
        return None
    if isinstance(v, RGBColor):
        return v
    if isinstance(v, str):
        # espera "RRGGBB"
        try:
            return RGBColor.from_string(v)
        except Exception:
            return None
    return None


def build_table(slide, element):
    """
    Reconstrói uma tabela do zero a partir do dicionário da função inspect.
    Inclui:
    - transparência real (noFill) quando background_color == None
    - remoção de table style (que pinta tudo de azul)
    - cores RGB / theme
    - bordas
    - alinhamento horizontal e vertical
    - runs, fontes, espaçamentos
    """

    left   = element["position"]["left"]
    top    = element["position"]["top"]
    width  = element["position"]["width"]
    height = element["position"]["height"]

    rows = element["rows"]
    cols = element["cols"]

    # ---------------------------------------------------------------------
    # CRIA A TABELA
    # ---------------------------------------------------------------------
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    # ---------------------------------------------------------------------
    # DESATIVA O TABLE STYLE (ESSENCIAL PARA NÃO FORÇAR FUNDO AZUL)
    # ---------------------------------------------------------------------
    try:
        tbl = table._tbl
        tblPr = tbl.tblPr
        if tblPr is not None:
            style_el = tblPr.find(qn('a:tblStyle'))
            if style_el is not None:
                tblPr.remove(style_el)
    except Exception as e:
        print("Aviso: não consegui remover tblStyle:", e)

    # ---------------------------------------------------------------------
    # DEFINIR ALTURAS E LARGURAS
    # ---------------------------------------------------------------------
    for i, rh in enumerate(element.get("row_heights", [])):
        if i < len(table.rows):
            table.rows[i].height = rh

    for j, cw in enumerate(element.get("col_widths", [])):
        if j < len(table.columns):
            table.columns[j].width = cw

    # ---------------------------------------------------------------------
    # PREENCHER CÉLULAS
    # ---------------------------------------------------------------------
    for r in range(rows):
        for c in range(cols):

            cell = table.cell(r, c)
            tf = cell.text_frame
            tf.clear()

            cdata = _normalize_cell_data(element["cells"][r][c], r, c)

            if isinstance(cdata, list):
                if len(cdata) == 0:
                    cdata = {}
                elif len(cdata) == 1 and isinstance(cdata[0], dict):
                    cdata = cdata[0]
                else:
                    raise ValueError(f"Estrutura inválida em cells[{r}][{c}]: {cdata}")

            bg = cdata.get("background_color")

            if bg is None:
                # Força a célula a não ter fill (a:noFill) via "transparency"
                try:
                    fill = cell.fill
                    fill.solid()
                    fill.fore_color.rgb = RGBColor(255, 255, 255)
                    fill.fore_color.transparency = 1.0
                except:
                    pass

            else:
                try:
                    fill = cell.fill
                    fill.solid()

                    if bg.get("type") == "rgb":
                        rgb = _rgb_value_to_rgbcolor(bg.get("value"))
                        if rgb is not None:
                            fill.fore_color.rgb = rgb
                    elif bg.get("type") == "theme":
                        # mantém seu contrato: bg["index"]
                        fill.fore_color.theme_color = bg.get("index")

                except Exception as e:
                    print("Erro cor fundo:", e)

            # ==============================================================
            # 2) BORDAS
            # ==============================================================

            borders = cdata.get("borders", {}) or {}

            for side in ("left", "right", "top", "bottom"):
                binfo = borders.get(side)
                if not binfo:
                    continue

                try:
                    border = getattr(cell.border, side)

                    if binfo.get("width"):
                        border.width = binfo["width"]

                    col = binfo.get("color")
                    if col:
                        if col.get("type") == "rgb":
                            rgb = _rgb_value_to_rgbcolor(col.get("value"))
                            if rgb is not None:
                                border.color.rgb = rgb
                        elif col.get("type") == "theme":
                            border.color.theme_color = col.get("index")

                except:
                    pass

            # ==============================================================
            # 3) ALINHAMENTO VERTICAL
            # ==============================================================

            va = _normalize_vertical_anchor(cdata.get("vertical_alignment"))
            if va is not None:
                try:
                    cell.vertical_anchor = va
                except:
                    pass

            # ==============================================================
            # 4) TEXTO + RUNS + ESPAÇAMENTO
            # ==============================================================

            first_p = True
            for pjson in (cdata.get("text", []) or []):
                if first_p:
                    p = tf.paragraphs[0]
                    first_p = False
                else:
                    p = tf.add_paragraph()

                # alinhamento horizontal
                try:
                    p.alignment = _normalize_pp_align(pjson.get("alignment"), PP_ALIGN.LEFT)
                except:
                    p.alignment = PP_ALIGN.LEFT

                # R U N S
                for rjson in (pjson.get("runs", []) or []):
                    run = p.add_run()
                    run.text = rjson.get("text", "")

                    if rjson.get("font_name") is not None:
                        run.font.name = rjson.get("font_name")

                    if rjson.get("font_size") is not None:
                        try:
                            run.font.size = Pt(rjson["font_size"])
                        except:
                            pass

                    run.font.bold = rjson.get("bold")
                    run.font.italic = rjson.get("italic")
                    run.font.underline = rjson.get("underline")

                    # cor do run
                    col = rjson.get("color")
                    if col:
                        try:
                            if col.get("type") == "rgb":
                                rgb = _rgb_value_to_rgbcolor(col.get("value"))
                                if rgb is not None:
                                    run.font.color.rgb = rgb
                            elif col.get("type") == "theme":
                                run.font.color.theme_color = col.get("index")
                        except:
                            pass

                # espaçamento
                try:
                    if pjson.get("line_spacing") is not None:
                        p.line_spacing = pjson["line_spacing"]
                except:
                    pass

                # (você comentou que precisa existir line_spacing_rule=None no dict;
                # aqui não é aplicado hoje, mas se quiser, é só descomentar)
                # try:
                #     if pjson.get("line_spacing_rule") is not None:
                #         p.line_spacing_rule = pjson["line_spacing_rule"]
                # except:
                #     pass

                try:
                    if pjson.get("space_before") is not None:
                        p.space_before = Pt(pjson["space_before"])
                except:
                    pass

                try:
                    if pjson.get("space_after") is not None:
                        p.space_after = Pt(pjson["space_after"])
                except:
                    pass

    # Remover sombra
    try:
        table_shape.shadow.inherit = False
        table_shape.shadow.visible = False
    except:
        pass

    return table_shape


##############################################
#   GROUP
##############################################

def build_group(slide, element, visited=None):
    if visited is None:
        visited = set()

    if id(element) in visited:
        print("[ERRO] Loop detectado no grupo.")
        return

    visited.add(id(element))

    for child in element.get("children", []):
        build_element(slide, child)


##############################################
#   BACKGROUND PICTURE
##############################################

from pptx.util import Inches, Pt


def build_background_picture(slide, bg):
    """
    bg pode ser:
      - string: caminho da imagem
      - dict de elemento com chave "image"
      - dict de background com chave "path"
      - dict de background com chave "image": { "path": ... }

    Garante que sempre passamos um path (str) para add_picture.
    """

    image_path = None

    # Caso 1: já é string (caminho)
    if isinstance(bg, str):
        image_path = bg

    # Caso 2: é dict
    elif isinstance(bg, dict):
        # elemento tipo picture/background_picture:
        # {"type": "...", "image": {"path": "...", ...}}
        if "image" in bg and isinstance(bg["image"], dict):
            image_path = bg["image"].get("path")

        # dicionário de background: {"path": "..."}
        if image_path is None:
            image_path = bg.get("path")

    if not image_path:
        print("[AVISO] build_background_picture: sem caminho de imagem válido:", bg)
        return None

    # insere a imagem (deixa o PPT definir o tamanho original)
    pic = slide.shapes.add_picture(
        image_path,
        left=0,
        top=0
    )

    # envia para trás de tudo
    try:
        spTree = slide.shapes._spTree
        spTree.remove(pic._element)
        spTree.insert(2, pic._element)  # logo após o bg nativo
    except Exception as e:
        print("Aviso ao reposicionar background:", e)

    return pic


from pptx.dml.color import RGBColor, MSO_THEME_COLOR
import re
from pptx.dml.color import RGBColor, MSO_THEME_COLOR

HEX_COLOR_RE = re.compile(r'^[0-9a-fA-F]{6}$')

def parse_color(color_info):
    """
    Converte QUALQUER estrutura de cor em um formato padronizado:
      Retorna:
        {"mode": "rgb", "value": RGBColor(...)}
        {"mode": "theme", "value": MSO_THEME_COLOR.ACCENT_X}
        OU None

    Aceita:
        "AE0029"
        {"type":"rgb","value":"AE0029"}
        {"type":"theme","name":"ACCENT_4","index":8}
        {"type":"rgb","value": {"type":"theme","name":"ACCENT_4"}} ← corrige automaticamente
    """
    if color_info is None:
        return None

    # ------------------------------
    # STRING HEX
    # ------------------------------
    if isinstance(color_info, str) and HEX_COLOR_RE.match(color_info):
        return {"mode": "rgb", "value": RGBColor.from_string(color_info)}

    # ------------------------------
    # DICIONÁRIO
    # ------------------------------
    if isinstance(color_info, dict):

        # Caso RGB normal
        if color_info.get("type") == "rgb":
            value = color_info.get("value")

            # Corrige caso value venha como {"type":"theme"...} por erro do inspector
            if isinstance(value, dict) and value.get("type") == "theme":
                # converte para theme por segurança
                theme_name = value.get("name")
                try:
                    theme_enum = getattr(MSO_THEME_COLOR, theme_name)
                    return {"mode": "theme", "value": theme_enum}
                except:
                    return None

            if isinstance(value, str) and HEX_COLOR_RE.match(value):
                return {"mode": "rgb", "value": RGBColor.from_string(value)}

            return None

        # Caso THEME
        if color_info.get("type") == "theme":
            theme_name = color_info.get("name")

            try:
                theme_enum = getattr(MSO_THEME_COLOR, theme_name)
                return {"mode": "theme", "value": theme_enum}
            except:
                return None

    # ------------------------------
    # Caso realmente não reconheça
    # ------------------------------
    return None

def apply_color_to_fill(fill, color_info):
    parsed = parse_color(color_info)
    if parsed is None:
        return

    mode = parsed["mode"]
    value = parsed["value"]

    if mode == "rgb":
        fill.fore_color.rgb = value
        return

    if mode == "theme":
        fill.fore_color.theme_color = value
        return

# ============================================================
# FUNÇÃO PRINCIPAL — reconstrução do background
# ============================================================

def build_background(slide, bg_info):
    """
    bg_info esperado:
        {
          "fill_type": "solid" | "gradient" | "picture" | "none",
          "color": {"type": "rgb"/"theme", ... }  OU None,
          "image": {...} OU None
        }

    OBS:
    - Background por imagem (picture) está DESABILITADO
    """

    fill = slide.background.fill
    fill_type = bg_info.get("fill_type")
    color     = bg_info.get("color")

    # ---------------------------------------------------------
    # 1) NONE – deixa default do tema
    # ---------------------------------------------------------
    if fill_type in ("none", None):
        try:
            fill.background()
        except:
            pass
        return

    # ---------------------------------------------------------
    # 2) SOLID
    # ---------------------------------------------------------
    if fill_type == "solid":
        fill.solid()
        apply_color_to_fill(fill, color)
        return

    # ---------------------------------------------------------
    # 3) GRADIENT  → fallback para solid
    # ---------------------------------------------------------
    if fill_type == "gradient":
        fill.solid()
        apply_color_to_fill(fill, color)
        return

    # ---------------------------------------------------------
    # 4) PICTURE — DESABILITADO
    # ---------------------------------------------------------
    if fill_type == "picture":
        # NÃO reconstrói imagem
        # Mantém o fundo original do slide/template
        try:
            fill.background()
        except:
            pass

        # opcional: log controlado
        # print("[INFO] Background picture ignorado por decisão de build.")
        return

    # ---------------------------------------------------------
    # 5) FALLBACK
    # ---------------------------------------------------------
    try:
        fill.background()
    except:
        pass


###########################
##### BUILDER PPT #########
###########################

from pptx import Presentation

# ---------------------------------------------------------------------
# 1. Decide automaticamente qual função executar
# ---------------------------------------------------------------------
def build_element(slide, element):
    t = element["type"]

    if t == "picture":
        return build_picture(slide, element)

    if t == "textbox":
        return build_textbox(slide, element)

    if t == "line":
        return build_line(slide, element)

    if t == "table":
        return build_table(slide, element)

    if t == "autoshape":
        return build_autoshape(slide, element)

    if t == "group":
        return build_group(slide, element)
    
    if t == "background_picture":
        build_background_picture(slide, element)


    print(f"[AVISO] Tipo não suportado: {t}")



# ---------------------------------------------------------------------
# 2. Reconstrói UM slide do dicionário
# ---------------------------------------------------------------------
def build_slide_from_dict(prs, slide_dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # BACKGROUND
    if "background" in slide_dict:
        build_background(slide, slide_dict["background"])

    # ELEMENTOS
    for element in slide_dict["elements"]:
        build_element(slide, element)

    return slide


# ---------------------------------------------------------------------
# 3. Gera a apresentação inteira
# ---------------------------------------------------------------------
def build_presentation(ppts_dict, output="presentation_rebuilt.pptx"):
    prs = Presentation()
    prs.slide_width = ppts_dict["slide_width"]
    prs.slide_height = ppts_dict["slide_height"]

    for slide_dict in ppts_dict["slides"]:
        build_slide_from_dict(prs, slide_dict)

    prs.save(output)
    return prs
