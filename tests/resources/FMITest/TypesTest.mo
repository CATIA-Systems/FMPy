within FMITest;
model TypesTest
  extends Modelica.Icons.Example;
  Modelica.Blocks.Sources.Sine sine
    annotation (Placement(transformation(extent={{-80,30},{-60,50}})));
  Modelica.Blocks.Sources.BooleanPulse booleanPulse
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  Modelica.Blocks.Sources.IntegerStep integerStep(height=2, startTime=2)
    annotation (Placement(transformation(extent={{-80,-50},{-60,-30}})));
  Types types annotation (Placement(transformation(extent={{-20,-10},{20,10}})));
equation
  connect(booleanPulse.y, types.'boolean_in')
    annotation (Line(points={{-59,0},{-22,0}}, color={255,0,255}));
  connect(sine.y, types.'real_in') annotation (Line(points={{-59,40},{-40,40},{
          -40,5},{-22,5}}, color={0,0,127}));
  connect(integerStep.y, types.'integer_in') annotation (Line(points={{-59,-40},
          {-40,-40},{-40,-5},{-22,-5}}, color={255,127,0}));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)),
    Diagram(coordinateSystem(preserveAspectRatio=false)),
    experiment(StopTime=10, __Dymola_Algorithm="Dassl"));
end TypesTest;
