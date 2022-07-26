within FMI.FMI3.Functions;
impure function FMI3ExitInitializationMode
  input Internal.ExternalFMU externalFMU;
    external"C" FMU_FMI3ExitInitializationMode(externalFMU) annotation (Library="ModelicaFMI");
end FMI3ExitInitializationMode;
