within FMI.FMI2.Functions;
impure function FMI2GetIntegerScalar
  input Internal.ExternalFMU externalFMU;
    input Integer vr;
    output Integer value;
    external"C" FMU_FMI2GetIntegerScalar(externalFMU, vr, value) annotation (Library="ModelicaFMI");
end FMI2GetIntegerScalar;
