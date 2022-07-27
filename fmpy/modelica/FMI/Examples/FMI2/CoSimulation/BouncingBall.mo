within FMI.Examples.FMI2.CoSimulation;
model BouncingBall
  extends Modelica.Icons.Example;
  FMUs.BouncingBall bouncingBall
    annotation (Placement(transformation(extent={{-20,-10},{20,10}})));
  annotation (experiment(StopTime=4, __Dymola_Algorithm="Dassl"),
      __Dymola_Commands(executeCall(
        ensureSimulated=true,
        autoRun=true) = {createPlot(
          id=1,
          position={75,75,1034,640},
          y={"bouncingBall.'h'","bouncingBall.'v'"},
          range={0.0,4.0,-5.0,3.5},
          grid=true,
          colors={{28,108,200},{238,46,47}},
          timeUnit="s")}));
end BouncingBall;
