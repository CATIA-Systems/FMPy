within FMITest.Models;
model Types
  Modelica.Blocks.Interfaces.RealInput real_in
    annotation (Placement(transformation(extent={{-140,40},{-100,80}})));
  Modelica.Blocks.Interfaces.BooleanInput boolean_in
    annotation (Placement(transformation(extent={{-140,-80},{-100,-40}})));
  Modelica.Blocks.Interfaces.IntegerInput integer_in
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealOutput real_out
    annotation (Placement(transformation(extent={{100,50},{120,70}})));
  Modelica.Blocks.Interfaces.IntegerOutput integer_out
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.BooleanOutput boolean_out
    annotation (Placement(transformation(extent={{100,-70},{120,-50}})));
equation
  connect(real_in, real_out)
    annotation (Line(points={{-120,60},{110,60}}, color={0,0,127}));
  connect(integer_in, integer_out)
    annotation (Line(points={{-120,0},{110,0}}, color={255,127,0}));
  connect(boolean_in, boolean_out)
    annotation (Line(points={{-120,-60},{110,-60}}, color={255,0,255}));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false), graphics={
                                Rectangle(
        extent={{-100,-100},{100,100}},
        lineColor={0,0,127},
        fillColor={255,255,255},
        fillPattern=FillPattern.Solid)}),
    Diagram(coordinateSystem(preserveAspectRatio=false)));
end Types;
