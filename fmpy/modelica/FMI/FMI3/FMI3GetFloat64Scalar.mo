within FMI.FMI3;
impure function FMI3GetFloat64Scalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  output Real value;
algorithm
  value := scalar(FMI3GetFloat64(
      externalFMU,
      {valueReference},
      1));
end FMI3GetFloat64Scalar;
