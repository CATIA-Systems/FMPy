within FMI.FMI3;
impure function FMI3EnterInitializationMode
  input Internal.ExternalFMU externalFMU;
  input Boolean toleranceDefined;
  input Real tolerance;
  input Real startTime;
  input Boolean stopTimeDefined;
  input Real stopTime;
  external"C" FMU_FMI3EnterInitializationMode(externalFMU, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime) annotation (Library="ModelicaFMI");
end FMI3EnterInitializationMode;
