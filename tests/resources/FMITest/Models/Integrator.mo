within FMITest.Models;
model Integrator
  Modelica.Blocks.Continuous.Integrator integrator
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Blocks.Interfaces.RealOutput y "Connector of Real output signal"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Sources.Constant const(k=1)
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
equation
  connect(integrator.y, y)
    annotation (Line(points={{11,0},{110,0}}, color={0,0,127}));
  connect(const.y, integrator.u)
    annotation (Line(points={{-59,0},{-12,0}}, color={0,0,127}));
  annotation (                                 experiment(
        __Dymola_fixedstepsize=0.1, __Dymola_Algorithm="Euler"), Icon(graphics=
         {                      Rectangle(
        extent={{-100,-100},{100,100}},
        lineColor={0,0,127},
        fillColor={255,255,255},
        fillPattern=FillPattern.Solid)}));
end Integrator;
