within FMI.FMI2.Functions;
impure function FMI2EnterEventMode
  input Internal.ExternalFMU externalFMU;
    external"C" FMU_FMI2EnterEventMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2EnterEventMode;
