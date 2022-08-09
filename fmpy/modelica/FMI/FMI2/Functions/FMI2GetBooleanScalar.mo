within FMI.FMI2.Functions;
impure function FMI2GetBooleanScalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  input Real t = 0;
  output Boolean value;
algorithm
  value :=scalar(FMI2GetBoolean(externalFMU, {valueReference}, 1));
end FMI2GetBooleanScalar;
