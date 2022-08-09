within FMI.FMI3.Functions;
impure function FMI3GetBooleanScalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  input Real t = 0;
  output Boolean value;
algorithm
  value :=scalar(Functions.FMI3GetBoolean(
      externalFMU,
      {valueReference},
      1));
end FMI3GetBooleanScalar;
