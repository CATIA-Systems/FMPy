within FMITest.Models;
model BouncingBall "A bouncing ball model to test state events"

  parameter Real e(min=0, max=1) = 0.8 "Coefficient of restitution";

  parameter Modelica.Units.SI.Velocity eps(min=0) = 1e-1 "Small velocity";

  Modelica.Units.SI.Height h(start=1.0, fixed=true) "Height of the ball";

  Modelica.Units.SI.Velocity v(start=0.0, fixed=true) "Velocity of the ball";

  Boolean done;

  Modelica.Blocks.Interfaces.RealOutput height "Height of the ball"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));

initial equation

  done = false;

equation

  v = der(h);

  der(v) = if done then 0 else -Modelica.Constants.g_n;

  when h < 0 then

    done = abs(v) < eps;

    reinit(v, -e * (if done then 0 else pre(v)));

    reinit(h, 0);

  end when;

  height = h;

  annotation (experiment(StopTime=4), Icon(graphics={
                                Rectangle(
        extent={{-100,-100},{100,100}},
        lineColor={0,0,127},
        fillColor={255,255,255},
        fillPattern=FillPattern.Solid)}));
end BouncingBall;
