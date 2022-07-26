within FMI.FMI2;
impure function FMI2GetRealScalar
  input Internal.ExternalFMU externalFMU;
    input Integer vr;
    input Real dummyTime = 0.0;
    output Real value;
    external"C" FMU_FMI2GetRealScalar(externalFMU, vr, value) annotation (Library="ModelicaFMI");
end FMI2GetRealScalar;
