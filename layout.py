from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET

def generate_layout_image(layout_xml, output_file, width=384, dpi=203):
    img = Image.new("L", (width, 1200), color=255)
    draw = ImageDraw.Draw(img)
    root = ET.fromstring(layout_xml)
    current_y = 0
    for line in root.findall("line"):
      line_height = 30
      for element in line:
        align = element.get("align", "left")
        if element.tag == "text":
          font_name = element.get('font', 'zpix.ttf')
          font_size = int(element.get('font_size', 18))
          font = ImageFont.truetype(font_name, font_size)
          text_content = element.text
          text_width, text_height = draw.textbbox((0, 0), text_content, font=font)[2:]
          if align == "left":
              text_x = 0
          elif align == "center":
              text_x = (width - text_width) // 2
          elif align == "right":
              text_x = width - text_width
          img.resize((width, current_y + text_height), Image.LANCZOS)
          draw.text((text_x, current_y), text_content, font=font, fill=0)
          line_height = max(line_height, text_height)
        elif element.tag == "image":
          image_path = element.get("src")
          image = Image.open(image_path)
          image = image.resize((width, int(width / image.width * image.height)), resample=Image.Resampling.LANCZOS)
          img.paste(image, (0, current_y))
          line_height = max(line_height, image.height)
      current_y += line_height
    
    img = img.crop((0, 0, width, current_y))
    img.save(output_file, dpi=(dpi, dpi))

layout_xml = """
<page>
  <line>
    <text align="left">--</text>
    <text align="center" font_size="62">Hello world</text>
    <text align="right">--</text>
  </line>
  
  <line>
    <text align="center" >你好</text>
  </line>
  
  <line>
    <image src="cat.jpg" />
  </line>
  
  <line>
    <text align="center">--</text>
  </line>
  
</page>
"""

generate_layout_image(layout_xml, "output.png")
