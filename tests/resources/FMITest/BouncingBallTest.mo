within FMITest;
model BouncingBallTest
  extends Modelica.Icons.Example;
  BouncingBall bouncingBall(loggingOn=true)
    annotation (Placement(transformation(extent={{-20,-10},{20,10}})));
  annotation (
    Icon(coordinateSystem(preserveAspectRatio=false)),
    Diagram(coordinateSystem(preserveAspectRatio=false)),
    experiment(StopTime=3, __Dymola_Algorithm="Dassl"));
end BouncingBallTest;
