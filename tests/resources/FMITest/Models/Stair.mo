within FMITest.Models;
block Stair "Generate a stair signal"
  extends Modelica.Blocks.Interfaces.SignalSource;

protected
  Integer count;

initial algorithm
  count := 0;

equation

  when integer(time) > pre(count) then
    count = pre(count) + 1;
  end when;

  y = count;

  annotation (experiment(StopTime=10));
end Stair;
