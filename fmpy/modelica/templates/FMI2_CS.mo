@@ extends "FMU.mo" @@
@@ block equations @@

initial algorithm

@@ for variable in parameters @@
  FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

  FMI2SetupExperiment(instance, tolerance > 0.0, tolerance, startTime, stopTime < Modelica.Constants.inf, stopTime);
  FMI2EnterInitializationMode(instance);

@@ for variable in real_inputs @@
  FMI2SetReal(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@_start'});
@@ endfor @@

  FMI2ExitInitializationMode(instance);

algorithm

  when sample(startTime, communicationStepSize) then

@@ for variable in inputs @@
    FMI2Set@=variable.type=@(instance, {@=variable.valueReference=@}, 1, {'@=variable.name=@'});
@@ endfor @@

    FMI2DoStep(instance, time, communicationStepSize, true);

@@ for variable in outputs @@
    '@=variable.name=@' = FMI2Get@=variable.type=@Scalar(instance, @=variable.valueReference=@);
@@ endfor @@

  end when;
@@ endblock @@