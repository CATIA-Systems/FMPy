within FMI.FMI2.Functions;
impure function FMI2ExitInitializationMode
  input Internal.ExternalFMU externalFMU;
    external"C" FMU_FMI2ExitInitializationMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI2ExitInitializationMode;
