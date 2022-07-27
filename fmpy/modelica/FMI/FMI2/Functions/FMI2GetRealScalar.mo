within FMI.FMI2.Functions;
impure function FMI2GetRealScalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  input Real t = 0;
  output Real value;
algorithm
  value :=scalar(FMI2GetReal(externalFMU, {valueReference}, 1));
end FMI2GetRealScalar;
