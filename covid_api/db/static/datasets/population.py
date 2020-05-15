population = dict(
  id='gibs-population',
  name='Population',
  type='raster',
  source=dict(
    type='raster',
    tiles=[
      'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/GPW_Population_Density_2020/default/2020-05-14T00:00:00Z/GoogleMapsCompatible_Level7/{z}/{y}/{x}.png'
    ]
  ),
  swatch=dict(color='#F55E2C', name='Orange'),
  legend=dict(
    type='gradient',
    min='less',
    max='more',
    stops=[
      '#FFEFCB',
      '#FBA54A',
      '#FB9F46',
      '#F35228',
      '#BD0026'
    ]
  ),
  info=None,
)
