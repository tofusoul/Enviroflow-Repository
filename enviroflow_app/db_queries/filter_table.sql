SELECT *
FROM {{ table_name }}
WHERE
  (
  {{ column_name }} ILIKE '{{ ilike_matches.pop(0) }}'
  {% if ilike_matches %}
    {% for str_match in ilike_matches %}
      OR {{ column_name }} ILIKE '{{ str_match }}'
    {% endfor %}
  {% endif %}
  )
  {% for str_match in ilike_exceptions %}
    AND {{ column_name }} NOT ILIKE '{{ str_match }}'
  {% endfor %}
