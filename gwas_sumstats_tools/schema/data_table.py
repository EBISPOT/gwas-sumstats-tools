"""
TODO petl validaiton

validate metadata
    - zero p
    - neglog10 p
validate headers
generate schema based on above
constraints = [
 dict(name='foo_int', field='foo', test=int),
 dict(name='bar_date', field='bar', test=etl.dateparser('%Y-%m-%d')),
 dict(name='baz_enum', field='baz', assertion=lambda v: v in ['Y', 'N']),
 dict(name='not_none', assertion=lambda row: None not in row),
 dict(name='qux_int', field='qux', test=int, optional=True),
 ]
problems = etl.validate(table, constraints=constraints, header=header)
"""
