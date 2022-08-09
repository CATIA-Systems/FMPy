within FMI.FMI3.Functions;
impure function FMI3GetInt32Scalar
  input Internal.ExternalFMU externalFMU;
  input Integer valueReference;
  input Real t = 0;
  output Integer value;
algorithm
  value :=scalar(Functions.FMI3GetInt32(
      externalFMU,
      {valueReference},
      1));
end FMI3GetInt32Scalar;
