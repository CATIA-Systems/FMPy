within FMI.Examples.FMI2.CoSimulation;
model Stair
  extends Modelica.Icons.Example;
  FMUs.Stair stair
    annotation (Placement(transformation(extent={{-20,-10},{20,10}})));
  annotation (experiment(StopTime=4, __Dymola_Algorithm="Dassl"),
      __Dymola_Commands(executeCall(
        ensureSimulated=true,
        autoRun=true) = {createPlot(
        id=1,
        position={177,225,1034,640},
        y={"stair.'counter'"},
        range={0.0,4.0,0.5,5.5},
        grid=true,
        colors={{28,108,200}},
        timeUnit="s")}
        "{createPlot(id=1, position={177,225,1034,640}, y={\"stair.'counter'\"}, range={0.0,4.0,0.5,5.5}, grid=true, colors={{28,108,200}}, timeUnit=\"s\")}"));
end Stair;
