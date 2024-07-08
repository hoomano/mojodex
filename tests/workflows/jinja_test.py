from jinja2 import Template

template = Template("""{% if not items %}items{%endif%}
                    """)

print(template.render(items=[]))