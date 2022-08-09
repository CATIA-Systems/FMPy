within FMI.FMI2.Functions;
impure function FMI2GetIntegerScalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  input Real t = 0;
  output Integer value;
algorithm
  value :=scalar(FMI2GetInteger(externalFMU, {valueReference}, 1));
end FMI2GetIntegerScalar;
