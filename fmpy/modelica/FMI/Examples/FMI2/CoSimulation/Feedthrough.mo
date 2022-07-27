within FMI.Examples.FMI2.CoSimulation;
model Feedthrough
  extends Modelica.Icons.Example;
  FMUs.Feedthrough feedthrough
    annotation (Placement(transformation(extent={{-20,-10},{20,10}})));
  Modelica.Blocks.Sources.Pulse pulse(
    amplitude=3,
    period=0.5,
    offset=-1.5)
    annotation (Placement(transformation(extent={{-80,10},{-60,30}})));
  Modelica.Blocks.Sources.Sine sine
    annotation (Placement(transformation(extent={{-80,50},{-60,70}})));
  Modelica.Blocks.Sources.BooleanPulse booleanPulse(period=1, startTime=1)
    annotation (Placement(transformation(extent={{-80,-70},{-60,-50}})));
  Modelica.Blocks.Sources.IntegerStep integerStep(
    height=3,
    offset=-1,
    startTime=2)
    annotation (Placement(transformation(extent={{-80,-30},{-60,-10}})));
equation
  connect(pulse.y, feedthrough.'Float64_discrete_input') annotation (Line(
        points={{-59,20},{-30,20},{-30,2},{-22,2}},
                                                  color={0,0,127}));
  connect(sine.y, feedthrough.'Float64_continuous_input') annotation (Line(
        points={{-59,60},{-28,60},{-28,6},{-22,6}}, color={0,0,127}));
  connect(booleanPulse.y, feedthrough.'Boolean_input') annotation (Line(points={{-59,-60},
          {-28,-60},{-28,-6},{-22,-6}},           color={255,0,255}));
  connect(integerStep.y, feedthrough.'Int32_input') annotation (Line(points={{-59,-20},
          {-30,-20},{-30,-2},{-22,-2}},      color={255,127,0}));
  annotation (experiment(StopTime=4, __Dymola_Algorithm="Dassl"),
      __Dymola_Commands(executeCall(
        ensureSimulated=true,
        autoRun=true) = {createPlot(
        id=1,
        position={0,0,2041,1796},
        y={"feedthrough.'Float64_continuous_input'",
          "feedthrough.'Float64_continuous_output'"},
        range={0.0,4.0,-2.0,2.5},
        autoscale=false,
        grid=true,
        subPlot=101,
        colors={{238,46,47},{28,108,200}},
        timeUnit="s"),createPlot(
        id=1,
        position={0,0,2041,1796},
        y={"feedthrough.'Boolean_input'","feedthrough.'Boolean_output'"},
        range={0.0,4.0,-2.0,2.5},
        autoscale=false,
        grid=true,
        subPlot=104,
        colors={{28,108,200},{28,108,200}},
        timeUnit="s"),createPlot(
        id=1,
        position={0,0,2041,1796},
        y={"feedthrough.'Int32_input'","feedthrough.'Int32_output'"},
        range={0.0,4.0,-2.0,2.5},
        autoscale=false,
        grid=true,
        subPlot=103,
        colors={{28,108,200},{28,108,200}},
        timeUnit="s"),createPlot(
        id=1,
        position={0,0,2041,1796},
        y={"feedthrough.'Float64_discrete_input'",
          "feedthrough.'Float64_discrete_output'"},
        range={0.0,4.0,-2.0,2.5},
        autoscale=false,
        grid=true,
        subPlot=102,
        colors={{0,140,72},{238,46,47}},
        timeUnit="s")}));
end Feedthrough;
