within FMITest;
model IntegratorTest
  extends Modelica.Icons.Example;
  Modelica.Blocks.Sources.Sine sine
    annotation (Placement(transformation(extent={{-60,0},{-40,20}})));
  Integrator integrator
    annotation (Placement(transformation(extent={{-20,0},{20,20}})));
equation
  connect(sine.y, integrator.'u')
    annotation (Line(points={{-39,10},{-22,10}}, color={0,0,127}));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)),
    Diagram(coordinateSystem(preserveAspectRatio=false)),
    experiment(StopTime=10, __Dymola_Algorithm="Dassl"));
end IntegratorTest;
