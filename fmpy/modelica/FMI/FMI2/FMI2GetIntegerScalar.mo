within FMI.FMI2;
impure function FMI2GetIntegerScalar
    input ExternalFMU externalFMU;
    input Integer vr;
    output Integer value;
    external"C" FMU_FMI2GetIntegerScalar(externalFMU, vr, value) annotation (Library="ModelicaFMI");
end FMI2GetIntegerScalar;
