within FMI.FMI2;
impure function FMI2EnterInitializationMode
  input Internal.ExternalFMU externalFMU;
    external"C" FMU_FMI2EnterInitializationMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2EnterInitializationMode;
