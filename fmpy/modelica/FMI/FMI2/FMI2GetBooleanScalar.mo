within FMI.FMI2;
impure function FMI2GetBooleanScalar
    input ExternalFMU externalFMU;
    input Integer vr;
    output Boolean value;
    external"C" FMU_FMI2GetBooleanScalar(externalFMU, vr, value) annotation (Library="ModelicaFMI");
end FMI2GetBooleanScalar;
